# https://github.com/Treeki/CylindricalEarth/blob/master/pynoexs.py
# https://github.com/Treeki/CylindricalEarth/blob/master/debug_tools.py

import time
import enum
import struct
import socket
import threading
from SMM2 import actors
from SMM2.expression_evaluator import handle_evaluate_expression
from SMM2.expressions import get_expressions

Status = enum.IntEnum('Status', ('STOPPED', 'RUNNING', 'PAUSED'), start=0)

Command = enum.IntEnum('Command', (
    'STATUS', 'POKE8', 'POKE16', 'POKE32', 'POKE64',
    'READ', 'WRITE', 'CONTINUE', 'PAUSE',
    'ATTACH', 'DETACH', 'QUERY_MEMORY', 'QUERY_MEMORY_MULTI',
    'CURRENT_PID', 'GET_ATTACHED_PID', 'GET_PIDS', 'GET_TITLEID',
    'DISCONNECT', 'READ_MULTI', 'SET_BREAKPOINT'))

MemoryType = enum.IntEnum('MemoryType', (
    'UNMAPPED', 'IO', 'NORMAL', 'CODE_STATIC', 'CODE_MUTABLE',
    'HEAP', 'SHARED', 'WEIRD_MAPPED', 'MODULE_CODE_STATIC', 'MODULE_CODE_MUTABLE',
    'IPC_BUFFER_0', 'MAPPED', 'THREAD_LOCAL', 'ISOLATED_TRANSFER', 'TRANSFER',
    'PROCESS', 'RESERVED', 'IPC_BUFFER_1', 'IPC_BUFFER_3', 'KERNEL_STACK',
    'CODE_READ_ONLY', 'CODE_WRITABLE'
), start=0)

class NoexsClient:
    def __init__(self, *args):
        if len(args) != 1:
            return None
        else:
            self.sock = socket.create_connection(args[0])
            self.address_lock = self.addr_lock(self, [])
            self.title_id = 0x01009B90006DC000
            self.attach(self.find_game(self.title_id))
            self.resume()
            self.binary = self.find_binary()
            self.expressions = get_expressions(self.binary)

    class addr_lock(threading.Thread):
        def __init__(self, *args):
            super().__init__()
            self.__flag = threading.Event()
            self.__flag.set()
            self.__running = threading.Event()
            self.__running.set()
            self.args = args

        def run(self):
            while self.__running.isSet():
                self.__flag.wait()
                for i in self.args[1]:
                    if i[1] == 1:
                        self.args[0].poke8(i[0], i[2])
                    elif i[1] == 2:
                        self.args[0].poke16(i[0], i[2])
                    elif i[1] == 4:
                        self.args[0].poke32(i[0], i[2])
                    elif i[1] == 8:
                        self.args[0].poke64(i[0], i[2])
                    else:
                        pass

        def pause(self):
            self.__flag.clear()

        def resume(self):
            self.__flag.set()

        def stop(self):
            self.__flag.set()
            self.__flag.clear()

        def add(self, *args):
            if len(args) != 3:
                return None
            else:
                for i in self.args[1]:
                    if i[0] == args[0]:
                        i[1] = args[1]
                        i[2] = args[2]
                        return None
                self.args[1].append([args[0], args[1], args[2]])

        def remove(self, *args):
            if len(args) != 1:
                return None
            else:
                for i in self.args[1]:
                    if i[0] == args[0]:
                        self.args[1].pop(self.args[1].index(i))
                    else:
                        pass

        def clear(self):
            self.args[1].clear()

    def _recvall(self, amount=None):
        if amount == None:
            return None
        else:
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
                pos+=indata[i+1]
            return bytes(outdata)

    def _assert_result_ok(self, throwaway=False):
        result = self._recv_result()
        if result != (0,0):
            if throwaway:
                self._recv_result()
            raise ValueError("connection error %d,%d" % result)

    def get_status(self):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<B", int(Command.STATUS)))
        self.address_lock.resume()
        status, major, minor, patch = struct.unpack("<BBBB", self._recvall(4))
        self._assert_result_ok()
        return (Status(status), major, minor, patch)

    def peek8(self, *args):
        if len(args) != 1:
            return None
        else:
            return struct.unpack("<B", self.read(args[0], 1))[0]

    def poke8(self, *args):
        if len(args) != 2:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQB", int(Command.POKE8), args[0], args[1]))
            self.address_lock.resume()
            self._assert_result_ok()

    def peek16(self, *args):
        if len(args) != 1:
            return None
        else:
            return struct.unpack("<H", self.read(args[0], 2))[0]

    def poke16(self, *args):
        if len(args) != 2:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQH", int(Command.POKE16), args[0], args[1]))
            self.address_lock.resume()
            self._assert_result_ok()

    def peek32(self, *args):
        if len(args) != 1:
            return None
        else:
            return struct.unpack("<I", self.read(args[0], 4))[0]

    def poke32(self, *args):
        if len(args) != 2:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQI", int(Command.POKE32), args[0], args[1]))
            self.address_lock.resume()
            self._assert_result_ok()

    def peek64(self, *args):
        if len(args) != 1:
            return None
        else:
            return struct.unpack("<Q", self.read(args[0], 8))[0]

    def poke64(self, *args):
        if len(args) != 2:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQQ", int(Command.POKE64), args[0], args[1]))
            self.address_lock.resume()
            self._assert_result_ok()

    def read(self, *args):
        if len(args) != 2:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQI", int(Command.READ), args[0], args[1]))
            self.address_lock.resume()
            self._assert_result_ok(throwaway=True)

            pos = 0
            result = b""
            while len(result) < args[1]:
                self._assert_result_ok(throwaway=True)
                result += self._recv_compressed()
            self._recv_result()
            return result

    def resume(self):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<B", int(Command.CONTINUE)))
        self.address_lock.resume()
        self._assert_result_ok()

    def pause(self):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<B", int(Command.PAUSE)))
        self.address_lock.resume()
        self._assert_result_ok()

    def attach(self, *args):
        if len(args) != 1:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQ", int(Command.ATTACH), args[0]))
            self.address_lock.resume()
            self._assert_result_ok()

    def detach(self):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<B", int(Command.DETACH)))
        self.address_lock.resume()
        self._assert_result_ok()

    def get_pids(self):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<B", int(Command.GET_PIDS)))
        self.address_lock.resume()
        count = struct.unpack("<I", self._recvall(4))[0]
        if count > 0:
            pids = list(struct.unpack("<%dQ" % count, self._recvall(8 * count)))
        else:
            pids = []
        self._assert_result_ok()
        return pids

    def get_title_id(self, *args):
        if len(args) != 1:
            return None
        else:
            self.address_lock.pause()
            self.sock.sendall(struct.pack("<BQ", int(Command.GET_TITLEID), args[0]))
            self.address_lock.resume()
            tid = struct.unpack("<Q", self._recvall(8))[0]
            self._assert_result_ok()
            return tid

    def get_memory_info(self, start=0, max=10000):
        self.address_lock.pause()
        self.sock.sendall(struct.pack("<BQI", int(Command.QUERY_MEMORY_MULTI), start, max))
        self.address_lock.resume()
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

    def find_game(self, *args):
        if len(args) != 1:
            return None
        else:
            for pid in reversed(self.get_pids()):
                if self.get_title_id(pid) == args[0]:
                    return pid
        return None

    def find_binary(self):
        self.code_static_rx = []
        self.code_static_r = []
        self.code_mutable = []
        for addr, size, typ, perm in self.get_memory_info():
            print('%10x %10x %d %r' % (addr, size, perm, typ))
            if typ == MemoryType.CODE_STATIC:
                if perm == 5:
                    self.code_static_rx.append((addr, size))
                elif perm == 1:
                    self.code_static_r.append((addr, size))
            elif typ == MemoryType.CODE_MUTABLE:
                self.code_mutable.append((addr, size))

        text, rodata, data = self.code_static_rx[1], self.code_static_r[1], self.code_mutable[1]
        print('\nTEXT: %10x .. %10x' % text)
        print('RODATA: %10x .. %10x' % rodata)
        print('DATA: %10x .. %10x' % data)

        return self.code_static_rx[0][0]+0x4000

    def peek_player_position_edit(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[11])
        return [addr, (self.peek32(addr), self.peek32(addr+0x4))]

    def poke_player_position_edit(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[11])
        if len(args[0]) != 2:
            return None
        else:
            for i in range(2):
                self.poke32(addr+0x4*i, args[0][i])

    def peek_player_position_play(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[13])
        return [addr, (self.peek32(addr), self.peek32(addr+0x4))]

    def poke_player_position_play(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[13])
        if len(args[0]) != 2:
            return None
        else:
            for i in range(2):
                self.poke32(addr+0x4*i, args[0][i])

    def peek_timer(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[0])
        return [addr, self.peek16(addr)]

    def poke_timer(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[0])
        self.poke16(addr, args[0])

    def peek_overworld_enemy_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[1])
        return [addr, self.peek32(addr)]

    def poke_overworld_enemy_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[1])
        self.poke32(addr, args[0])

    def peek_subworld_enemy_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[2])
        return [addr, self.peek32(addr)]

    def poke_subworld_enemy_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[2])
        self.poke32(addr, args[0])

    def peek_overworld_item_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[3])
        return [addr, self.peek32(addr)]

    def poke_overworld_item_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[3])
        self.poke32(addr, args[0])

    def peek_subworld_item_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[4])
        return [addr, self.peek32(addr)]

    def poke_subworld_item_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[4])
        self.poke32(addr, args[0])

    def peek_overworld_block_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[5])
        return [addr, self.peek32(addr)]

    def poke_overworld_block_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[5])
        self.poke32(addr, args[0])

    def peek_subworld_block_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[6])
        return [addr, self.peek32(addr)]

    def poke_subworld_block_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[6])
        self.poke32(addr, args[0])

    def peek_overworld_tile_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[7])
        return [addr, self.peek32(addr)]

    def poke_overworld_tile_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[7])
        self.poke32(addr, args[0])

    def peek_subworld_tile_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[8])
        return [addr, self.peek32(addr)]

    def poke_subworld_tile_count(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[8])
        self.poke32(addr, args[0])

    def peek_newest_overworld_actor_addr(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[9])
        return addr

    def peek_newest_subworld_actor_addr(self, *args):
        addr = handle_evaluate_expression(self, self.expressions[10])
        return addr

    class newest_overworld_actor:
        def __init__(self, *args):
            if len(args) != 2:
                return None
            else:
                self.args = args
                self.update()

        def update(self):
            self.addr = self.args[0].peek_newest_overworld_actor_addr()
            print("\n%08x" % self.peek_pos_x()[1])
            print("%08x" % self.peek_pos_y()[1])
            print("%08x" % self.peek_width()[1])
            print("%08x" % self.peek_height()[1])
            print("%08x %08x" % tuple(self.peek_flags()[1]))
            print("%08x" % self.peek_extended_data()[1])
            print("%08x %08x %08x %08x" % tuple(self.peek_types()[1]))
            print("%08x %08x %08x %08x %08x %08x %08x %08x" % tuple(self.peek_placement_flags()[1]))

        def peek_pos_x(self):
            return [self.addr, self.args[0].peek32(self.addr)]

        def poke_pos_x(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, args[0])

        def move_pixel_left(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])-args[0]))

        def move_pixel_right(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])+args[0]))

        def move_tile_left(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])-16.0*args[0]))

        def move_tile_right(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])+16.0*args[0]))

        def peek_pos_y(self):
            return [self.addr+0x4, self.args[0].peek32(self.addr+0x4)]

        def poke_pos_y(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, args[0])

        def move_pixel_up(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])+args[0]))

        def move_pixel_down(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])-args[0]))

        def move_tile_up(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])+16.0*args[0]))

        def move_tile_down(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])-16.0*args[0]))

        def peek_width(self):
            return [self.addr+0xC, self.args[0].peek32(self.addr+0xC)]

        def poke_width(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0xC, args[0])

        def peek_height(self):
            return [self.addr+0x10, self.args[0].peek32(self.addr+0x10)]

        def poke_height(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x10, args[0])

        def peek_flags(self):
            return [self.addr+0x14, [self.args[0].peek32(self.addr+0x14+4*i) for i in range(2)]]

        def poke_flags(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 2:
                    return None
                else:
                    for i in range(2):
                        self.args[0].poke32(self.addr+0x14+4*i, args[0][i])

        def peek_extended_data(self):
            return [self.addr+0x1C, self.args[0].peek32(self.addr+0x1C)]

        def poke_extended_data(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x1C, args[0])

        def peek_types(self):
            return [self.addr+0x20, [self.args[0].peek8(self.addr+0x20+i) for i in range(4)]]

        def poke_types(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 4:
                    return None
                else:
                    for i in range(4):
                        self.args[0].poke8(self.addr+0x20+i, args[0][i])

        def peek_placement_flags(self):
            return [self.addr+0x210, [self.args[0].peek32(self.addr+0x210+4*i) for i in range(8)]]

        def poke_placement_flags(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 8:
                    return None
                else:
                    for i in range(8):
                        self.args[0].poke32(self.addr+0x210+4*i, args[0][i])

    class newest_subworld_actor:
        def __init__(self, *args):
            if len(args) != 2:
                return None
            else:
                self.args = args
                self.update()

        def update(self):
            self.addr = self.args[0].peek_newest_subworld_actor_addr()
            print("\n%08x" % self.peek_pos_x()[1])
            print("%08x" % self.peek_pos_y()[1])
            print("%08x" % self.peek_width()[1])
            print("%08x" % self.peek_height()[1])
            print("%08x %08x" % tuple(self.peek_flags()[1]))
            print("%08x" % self.peek_extended_data()[1])
            print("%08x %08x %08x %08x" % tuple(self.peek_types()[1]))
            print("%08x %08x %08x %08x %08x %08x %08x %08x" % tuple(self.peek_placement_flags()[1]))

        def peek_pos_x(self):
            return [self.addr, self.args[0].peek32(self.addr)]

        def poke_pos_x(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, args[0])

        def move_pixel_right(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])+args[0]))

        def move_tile_left(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])-16.0*args[0]))

        def move_tile_right(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr, float_to_hex(hex_to_float(self.peek_pos_x()[1])+16.0*args[0]))

        def peek_pos_y(self):
            return [self.addr+0x4, self.args[0].peek32(self.addr+0x4)]

        def poke_pos_y(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, args[0])

        def move_pixel_up(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])+args[0]))

        def move_pixel_down(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])-args[0]))

        def move_tile_up(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])+16.0*args[0]))

        def move_tile_down(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x4, float_to_hex(hex_to_float(self.peek_pos_y()[1])-16.0*args[0]))

        def peek_width(self):
            return [self.addr+0xC, self.args[0].peek32(self.addr+0xC)]

        def poke_width(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0xC, args[0])

        def peek_height(self):
            return [self.addr+0x10, self.args[0].peek32(self.addr+0x10)]

        def poke_height(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x10, args[0])

        def peek_flags(self):
            return [self.addr+0x14, [self.args[0].peek32(self.addr+0x14+4*i) for i in range(2)]]

        def poke_flags(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 2:
                    return None
                else:
                    for i in range(2):
                        self.args[0].poke32(self.addr+0x14+4*i, args[0][i])

        def peek_extended_data(self):
            return [self.addr+0x1C, self.args[0].peek32(self.addr+0x1C)]

        def poke_extended_data(self, *args):
            if len(args) != 1:
                return None
            else:
                self.args[0].poke32(self.addr+0x1C, args[0])

        def peek_types(self):
            return [self.addr+0x20, [self.args[0].peek8(self.addr+0x20+i) for i in range(4)]]

        def poke_types(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 4:
                    return None
                else:
                    for i in range(4):
                        self.args[0].poke8(self.addr+0x20+i, args[0][i])

        def peek_placement_flags(self):
            return [self.addr+0x210, [self.args[0].peek32(self.addr+0x210+4*i) for i in range(8)]]

        def poke_placement_flags(self, *args):
            if len(args) != 1:
                return None
            else:
                if len(args[0]) != 8:
                    return None
                else:
                    for i in range(8):
                        self.args[0].poke32(self.addr+0x210+4*i, args[0][i])

def float_to_hex(*args):
    if len(args) != 1:
        return None
    else:
        return struct.unpack('<I', struct.pack('<f', args[0]))[0]

def hex_to_float(*args):
    if len(args) != 1:
        return None
    else:
        return struct.unpack('!f', struct.pack('>I', args[0]))[0]

if __name__ == "__main__":
    nx = NoexsClient(["192.168.1.5", "7331"])

    print()
    print("%08x" % nx.peek_timer()[1])
    print("%08x %08x" % (nx.peek_overworld_enemy_count()[1], nx.peek_subworld_enemy_count()[1]))
    print("%08x %08x" % (nx.peek_overworld_item_count()[1], nx.peek_subworld_item_count()[1]))
    print("%08x %08x" % (nx.peek_overworld_block_count()[1], nx.peek_subworld_block_count()[1]))
    print("%08x %08x" % (nx.peek_overworld_tile_count()[1], nx.peek_subworld_tile_count()[1]))

    newest_overworld_actor = nx.newest_overworld_actor(nx, nx.expressions)

    print()

    newest_subworld_actor = nx.newest_subworld_actor(nx, nx.expressions)
    nx.address_lock.start()
    address_lock = nx.address_lock
