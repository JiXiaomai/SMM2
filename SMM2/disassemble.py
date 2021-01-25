import subprocess
import capstone

ARCH = capstone.CS_ARCH_ARM64
MODE = capstone.CS_MODE_LITTLE_ENDIAN

CS = capstone.Cs(ARCH, MODE)

def disassemble(ASSEMBLY_HEXSTRING, START_ADDRESS):
    OUT = []
    for (ADDRESS, SIZE, MNEMONIC, OP_STR) in CS.disasm_lite(CODE, 0):
        OUT.append([ADDRESS, SIZE, MNEMONIC, OP_STR])
    return OUT

def assemble(ASSEMBLY_STRING, START_ADDRESS):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    output = subprocess.Popen(["kstool.exe"]+["arm64", ASSEMBLY_STRING, START_ADDRESS], stdout=subprocess.PIPE, startupinfo=startupinfo).communicate()[0].decode("utf-8")
    idx1 = output.rindex("[")
    idx2 = output.rindex("]")
    split = ["0x", output[idx1+1:idx2].translate({ord(c):None for c in ' \n\t\r'})]
    return "".join(split)
