# https://github.com/Treeki/CylindricalEarth/blob/master/pynoexs.py
# https://github.com/Treeki/CylindricalEarth/blob/master/debug_tools.py

import socket
import struct
import enum
import time
import threading
from SMM2 import sprites
from SMM2 import expression_evaluator
from SMM2 import expressions

Status = enum.IntEnum("Status", ("STOPPED", "RUNNING", "PAUSED"), start=0)

Command = enum.IntEnum("Command", (
    "STATUS", "POKE8", "POKE16", "POKE32", "POKE64",
    "READ", "WRITE", "CONTINUE", "PAUSE",
    "ATTACH", "DETACH", "QUERY_MEMORY", "QUERY_MEMORY_MULTI",
    "CURRENT_PID", "GET_ATTACHED_PID", "GET_PIDS", "GET_TITLEID",
    "DISCONNECT", "READ_MULTI", "SET_BREAKPOINT"))

MemoryType = enum.IntEnum("MemoryType", (
    "UNMAPPED", "IO", "NORMAL", "CODE_STATIC", "CODE_MUTABLE",
    "HEAP", "SHARED", "WEIRD_MAPPED", "MODULE_CODE_STATIC", "MODULE_CODE_MUTABLE",
    "IPC_BUFFER_0", "MAPPED", "THREAD_LOCAL", "ISOLATED_TRANSFER", "TRANSFER",
    "PROCESS", "RESERVED", "IPC_BUFFER_1", "IPC_BUFFER_3", "KERNEL_STACK",
    "CODE_READ_ONLY", "CODE_WRITABLE"
), start=0)

class NoexsClient:
    def __init__(self, address):
        self.sock = socket.create_connection(address)

    def _recvall(self, amount):
        buf = b""
        while len(buf) < amount:
            buf += self.sock.recv(amount-len(buf))
        return buf

    def _recv_result(self):
        value = struct.unpack("<I", self._recvall(4))[0]
        mod = value & 0x1FF
        desc = (value >> 9) & 0x1FFF
        return (mod, desc)

    def _recv_compressed(self):
        flag, dlen = struct.unpack("<BI", self._recvall(5))
        if flag == 0:
            return self._recvall(dlen)
        else:
            outdata = bytearray(dlen)
            indata = self._recvall(struct.unpack("<I", self._recvall(4))[0])
            pos = 0
            for i in range(0, len(indata), 2):
                for j in range(indata[i+1]):
                    outdata[pos+j] = indata[i]
                pos += indata[i+1]
            return bytes(outdata)

    def _assert_result_ok(self, throwaway=False):
        result = self._recv_result()
        if result != (0,0):
            if throwaway:
                self._recv_result()
            raise ValueError("connection error %d,%d" % result)

    def get_status(self):
        self.sock.sendall(struct.pack("<B", int(Command.STATUS)))
        status, major, minor, patch = struct.unpack("<BBBB", self._recvall(4))
        self._assert_result_ok()
        return (Status(status), major, minor, patch)

    def poke8(self, addr, value):
        self.sock.sendall(struct.pack("<BQB", int(Command.POKE8), addr, value))
        self._assert_result_ok()

    def poke16(self, addr, value):
        self.sock.sendall(struct.pack("<BQH", int(Command.POKE16), addr, value))
        self._assert_result_ok()

    def poke32(self, addr, value):
        self.sock.sendall(struct.pack("<BQI", int(Command.POKE32), addr, value))
        self._assert_result_ok()

    def poke64(self, addr, value):
        self.sock.sendall(struct.pack("<BQQ", int(Command.POKE64), addr, value))
        self._assert_result_ok()

    def peek8(self, addr):
        return struct.unpack("<B", self.read(addr, 1))[0]

    def peek16(self, addr):
        return struct.unpack("<H", self.read(addr, 2))[0]

    def peek32(self, addr):
        return struct.unpack("<I", self.read(addr, 4))[0]

    def peek64(self, addr):
        return struct.unpack("<Q", self.read(addr, 8))[0]

    def read(self, addr, size):
        self.sock.sendall(struct.pack("<BQI", int(Command.READ), addr, size))
        self._assert_result_ok(throwaway=True)

        pos = 0
        result = b""
        while len(result) < size:
            self._assert_result_ok(throwaway=True)
            result += self._recv_compressed()
        self._recv_result()
        return result

    def resume(self):
        self.sock.sendall(struct.pack("<B", int(Command.CONTINUE)))
        self._assert_result_ok()

    def pause(self):
        self.sock.sendall(struct.pack("<B", int(Command.PAUSE)))
        self._assert_result_ok()

    def attach(self, pid):
        self.sock.sendall(struct.pack("<BQ", int(Command.ATTACH), pid))
        self._assert_result_ok()

    def detach(self):
        self.sock.sendall(struct.pack("<B", int(Command.DETACH)))
        self._assert_result_ok()

    def get_pids(self):
        self.sock.sendall(struct.pack("<B", int(Command.GET_PIDS)))
        count = struct.unpack("<I", self._recvall(4))[0]
        if count > 0:
            pids = list(struct.unpack("<%dQ" % count, self._recvall(8*count)))
        else:
            pids = []
        self._assert_result_ok()
        return pids

    def get_title_id(self, pid):
        self.sock.sendall(struct.pack("<BQ", int(Command.GET_TITLEID), pid))
        tid = struct.unpack("<Q", self._recvall(8))[0]
        self._assert_result_ok()
        return tid

    def get_memory_info(self, start=0, max=10000):
        self.sock.sendall(struct.pack("<BQI", int(Command.QUERY_MEMORY_MULTI), start, max))
        results = []
        for i in range(max):
            addr, size, typ, perm = struct.unpack("<QQII", self._recvall(24))
            typ = MemoryType(typ)
            self._assert_result_ok()
            if typ == MemoryType.RESERVED:
                break
            else:
                results.append((addr, size, typ, perm))
        self._recv_result()
        return results

    def find_game(self, title_id):
        for pid in reversed(self.get_pids()):
            if self.get_title_id(pid) == title_id:
                return pid
        return None

    def find_binary(self):
        self.code_static_rx = []
        self.code_static_r = []
        self.code_mutable = []

        for addr, size, typ, perm in self.get_memory_info():
            if typ == MemoryType.CODE_STATIC:
                if perm == 5:
                    self.code_static_rx.append((addr,size))
                elif perm == 1:
                    self.code_static_r.append((addr,size))
            elif typ == MemoryType.CODE_MUTABLE:
                self.code_mutable.append((addr, size))

        text, rodata, data = self.code_static_rx[1], self.code_static_r[1], self.code_mutable[1]
        print("TEXT: %10x .. %10x" % text)
        print("RODATA: %10x .. %10x" % rodata)
        print("DATA: %10x .. %10x" % data)

        return self.code_static_rx[0][0]+0x4000

    def peek_timer(self):
        addr = expression_evaluator.evaluate_expression(self, self.expressions["timer"][0])
        return [addr, self.peek16(addr)]

    def poke_timer(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["timer"][0])
            self.poke16(addr, value)

    def peek_actor_count_overworld(self):
        addr1 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_enemy_count"][0])
        addr2 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_item_count"][0])
        addr3 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_block_count"][0])
        addr4 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_tile_count"][0])
        return {
            "overworld_enemy_count": [addr1, self.peek32(addr1)],
            "overworld_item_count": [addr2, self.peek32(addr2)],
            "overworld_block_count": [addr3, self.peek32(addr3)],
            "overworld_tile_count": [addr4, self.peek32(addr4)]
        }

    def poke_overworld_enemy_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_enemy_count"][0])
            self.nx.poke32(addr, value)

    def poke_overworld_item_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_item_count"][0])
            self.nx.poke32(addr, value)

    def poke_overworld_block_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_block_count"][0])
            self.nx.poke32(addr, value)

    def poke_overworld_tile_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_tile_count"][0])
            self.nx.poke32(addr, value)

    def peek_newest_actor_addr_overworld(self):
        addr = expression_evaluator.evaluate_expression(self, self.expressions["newest_overworld_actor"][0])
        return addr

    class newest_overworld_actor:
        def __init__(self, nx):
            self.nx = nx
            self.update()

        def update(self):
            self.addr = self.nx.peek_newest_actor_addr_overworld()
            self.position = {
                "x": self.nx.peek32(self.addr),
                "y": self.nx.peek32(self.addr+0x4),
                "z": self.nx.peek32(self.addr+0x4)
            }
            self.size = {
                "x": self.nx.peek32(self.addr+0xC),
                "y": self.nx.peek32(self.addr+0x10)
            }
            self.flags = {
                "parent": self.nx.peek32(self.addr+0x14),
                "child": self.nx.peek32(self.addr+0x18)
            }
            self.extended_data = self.nx.peek32(self.addr+0x1C)
            self.types = {
                "parent": [
                    self.nx.peek8(self.addr+0x20),
                    self.nx.peek8(self.addr+0x21)
                ],
                "child": [
                    self.nx.peek8(self.addr+0x22),
                    self.nx.peek8(self.addr+0x23)
                ]
            }
            self.placement_flags = []
            for i in range(8):
                self.placement_flags.append(self.nx.peek32(self.addr+0x210+i))

        def poke_pos_x(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr, value)

        def poke_pos_y(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x4, value)

        def poke_pos_z(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x8, value)

        def poke_width(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0xC, value)

        def poke_height(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x10, value)

        def poke_parent_flags(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x14, value)

        def poke_child_flags(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x18, value)

        def poke_extended_data(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x1C, value)

        def poke_parent_type(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke8(self.addr+0x20, value)

        def poke_child_type(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke8(self.addr+0x22, value)

        def poke_placement_flags(self, placement_flags):
            if not len(placement_flags) == 8:
                return None
            else:
                for i in range(8):
                    self.nx.poke32(self.addr+0x210+i, placement_flags[i])

    def peek_actor_count_subworld(self):
        addr1 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_enemy_count"][0])
        addr2 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_item_count"][0])
        addr3 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_block_count"][0])
        addr4 = expression_evaluator.evaluate_expression(self, self.expressions["overworld_tile_count"][0])
        return {
            "overworld_enemy_count": [addr1, self.peek32(addr1)],
            "overworld_item_count": [addr2, self.peek32(addr2)],
            "overworld_block_count": [addr3, self.peek32(addr3)],
            "overworld_tile_count": [addr4, self.peek32(addr4)]
        }

    def poke_subworld_enemy_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_enemy_count"][0])
            self.nx.poke32(addr, value)

    def poke_subworld_item_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_item_count"][0])
            self.nx.poke32(addr, value)

    def poke_subworld_block_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_block_count"][0])
            self.nx.poke32(addr, value)

    def poke_subworld_tile_count(self, value=None):
        if value == None:
            return None
        else:
            addr = expression_evaluator.evaluate_expression(self, self.expressions["overworld_tile_count"][0])
            self.nx.poke32(addr, value)

    def peek_newest_actor_addr_subworld(self):
        addr = expression_evaluator.evaluate_expression(self, self.expressions["newest_subworld_actor"][0])
        return addr

    class newest_subworld_actor:
        def __init__(self, nx):
            self.nx = nx
            self.update()

        def update(self):
            self.addr = self.nx.peek_newest_actor_addr_subworld()
            self.position = {
                "x": self.nx.peek32(self.addr),
                "y": self.nx.peek32(self.addr+0x4),
                "z": self.nx.peek32(self.addr+0x4)
            }
            self.size = {
                "x": self.nx.peek32(self.addr+0xC),
                "y": self.nx.peek32(self.addr+0x10)
            }
            self.flags = {
                "parent": self.nx.peek32(self.addr+0x14),
                "child": self.nx.peek32(self.addr+0x18)
            }
            self.extended_data = self.nx.peek32(self.addr+0x1C)
            self.types = {
                "parent": [
                    self.nx.peek8(self.addr+0x20),
                    self.nx.peek8(self.addr+0x21)
                ],
                "child": [
                    self.nx.peek8(self.addr+0x22),
                    self.nx.peek8(self.addr+0x23)
                ]
            }
            self.placement_flags = []
            for i in range(8):
                self.placement_flags.append(self.nx.peek32(self.addr+0x210+i))

        def poke_pos_x(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr, value)

        def poke_pos_y(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x4, value)

        def poke_pos_z(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x8, value)

        def poke_width(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0xC, value)

        def poke_height(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x10, value)

        def poke_parent_flags(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x14, value)

        def poke_child_flags(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x18, value)

        def poke_extended_data(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke32(self.addr+0x1C, value)

        def poke_parent_type(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke8(self.addr+0x20, value)

        def poke_child_type(self, value=None):
            if value == None:
                return None
            else:
                self.nx.poke8(self.addr+0x22, value)

        def poke_placement_flags(self, placement_flags):
            if not len(placement_flags) == 8:
                return None
            else:
                for i in range(8):
                    self.nx.poke32(self.addr+0x210+i, placement_flags[i])

def float_to_hex(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def hex_to_float(h):
    return struct.unpack('!f', struct.pack('>I', h))[0]

def main():
    nx = NoexsClient(["192.168.1.5", "7331"])
    nx.attach(nx.find_game(title_id))
    nx.resume()
    return nx, nx.find_binary()

if __name__ == "__main__":
    title_id = 0x01009B90006DC000
    nx, binary = main()
    nx.expressions = expressions.expressions(binary)
    print("#%s#" % ("="*30))
    for i in range(1, 6):
        print("SEARCHING FOR OVERWORLD ACTORS... (ATTEMPT %s/5)" % i)
        try:
            newest_overworld_actor = nx.newest_overworld_actor(nx) # newest actor placed in the overworld editor
            print("OVERWORLD ACTORS HAVE BEEN FOUND!")
            time.sleep(1)
            break
        except ValueError:
            time.sleep(1)
            if i != 5:
                pass
            else:
                print("OVERWORLD ACTORS COULD NOT BE FOUND!")

    for i in range(1, 6):
        print("SEARCHING FOR SUBWORLD ACTORS... (ATTEMPT %s/5)" % i)
        try:
            newest_subworld_actor = nx.newest_subworld_actor(nx) # newest actor placed in the subworld editor
            print("SUBWORLD ACTORS HAVE BEEN FOUND!")
            time.sleep(1)
            break
        except ValueError:
            time.sleep(1)
            if i != 5:
                pass
            else:
                print("SUBWORLD ACTORS COULD NOT BE FOUND!")
