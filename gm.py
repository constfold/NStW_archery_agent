from typing import Optional
from dataclasses import dataclass
import struct
from enum import IntEnum


class Bytecode(IntEnum):
    BC_GETDOT = 0
    BC_SETDOT = 1
    BC_GETIND = 2
    BC_SETIND = 3
    BC_OP_ADD = 4
    BC_OP_SUB = 5
    BC_OP_MUL = 6
    BC_OP_DIV = 7
    BC_OP_REM = 8
    BC_BIT_OR = 9
    BC_BIT_XOR = 10
    BC_BIT_AND = 11
    BC_BIT_SHL = 12
    BC_BIT_SHR = 13
    BC_BIT_INV = 14
    BC_OP_LT = 15
    BC_OP_GT = 16
    BC_OP_LTE = 17
    BC_OP_GTE = 18
    BC_OP_EQ = 19
    BC_OP_NEQ = 20
    BC_OP_NEG = 21
    BC_OP_POS = 22
    BC_OP_NOT = 23
    BC_NOP = 24
    BC_LINE = 25
    BC_BRA = 26
    BC_BRZ = 27
    BC_BRNZ = 28
    BC_BRZK = 29
    BC_BRNZK = 30
    BC_CALL = 31
    BC_RET = 32
    BC_RETV = 33
    BC_FOREACH = 34
    BC_POP = 35
    BC_POP2 = 36
    BC_DUP = 37
    BC_DUP2 = 38
    BC_SWAP = 39
    BC_PUSHNULL = 40
    BC_PUSHINT = 41
    BC_PUSHINT0 = 42
    BC_PUSHINT1 = 43
    BC_PUSHFP = 44
    BC_PUSHSTR = 45
    BC_PUSHTBL = 46
    BC_PUSHFN = 47
    BC_PUSHTHIS = 48
    BC_GETLOCAL = 49
    BC_SETLOCAL = 50
    BC_GETGLOBAL = 51
    BC_SETGLOBAL = 52
    BC_GETTHIS = 53
    BC_SETTHIS = 54
    BC_FORK = 55


@dataclass
class GmHeader:
    magic: bytes
    flags: int
    st_offset: int
    sc_offset: int
    fn_offset: int


@dataclass
class GmFunctionHeader:
    magic: bytes
    id: int
    flags: int
    numParams: int
    numLocals: int
    baseClassNumber: int
    maxStackSize: int
    byteCodeLen: int


@dataclass
class GmLineInfo:
    byteCodeAddress: int
    lineNumber: int


@dataclass
class GmFunction:
    header: GmFunctionHeader
    bytecode: bytes
    debugNameStringOffset: int
    baseClassNameOffset: list[int]
    lineInfoCount: int
    lineInfo: list[GmLineInfo]
    symbolStringOffset: list[int]


class GmStringTable:
    data: bytes

    def __init__(self, data) -> None:
        self.data = data

    def __getitem__(self, offset):
        return self.data[offset:].split(b"\0", 1)[0].decode("utf-8")

    def __repr__(self) -> str:
        return f"GmStringTable({self.data!r})"


@dataclass
class GmSourceCode:
    flags: int
    source: bytes


@dataclass
class GmLib:
    header: GmHeader
    sourceCode: GmSourceCode
    stringTable: GmStringTable
    functions: list[GmFunction]


def read_gm_lib(lib: bytes):
    header_data = lib[:20]
    header = GmHeader(*struct.unpack("<4sIIII", header_data[:]))

    assert header.magic == b"gml0"
    assert header.flags & 1 == 1, "Only support debug lib"

    st_data = lib[header.st_offset :]
    string_table_size = int.from_bytes(st_data[:4], "little")
    string_table = GmStringTable(st_data[4 : 4 + string_table_size])

    sc_data = lib[header.sc_offset :]
    source_sz = int.from_bytes(sc_data[:4], "little")
    source_flags = int.from_bytes(sc_data[4:8], "little")

    source = GmSourceCode(source_flags, sc_data[8 : 8 + source_sz])

    fn_data = lib[header.fn_offset :]
    func_num = int.from_bytes(fn_data[:4], "little")
    fn_data = fn_data[4:]

    functions = []
    for _ in range(func_num):
        func_header_data = fn_data[:32]
        func_header = GmFunctionHeader(
            *struct.unpack("<4sIIIIIII", func_header_data[:32])
        )
        assert func_header.magic == b"func"

        func_bytecode = fn_data[32 : 32 + func_header.byteCodeLen]

        fn_data = fn_data[32 + func_header.byteCodeLen :]
        func_debugNameStringOffset = int.from_bytes(fn_data[:4], "little")
        fn_data = fn_data[4:]

        func_baseClassNameOffset = []
        for _ in range(func_header.baseClassNumber):
            func_baseClassNameOffset.append(int.from_bytes(fn_data[:4], "little"))
            fn_data = fn_data[4:]

        func_lineInfoCount = int.from_bytes(fn_data[:4], "little")

        fn_data = fn_data[4:]
        func_lineInfo = []
        for _ in range(func_lineInfoCount):
            func_lineInfo.append(GmLineInfo(*struct.unpack("<II", fn_data[:8])))
            fn_data = fn_data[8:]

        func_symbolStringOffset = []
        for _ in range(func_header.numParams + func_header.numLocals):
            func_symbolStringOffset.append(int.from_bytes(fn_data[:4], "little"))
            fn_data = fn_data[4:]

        functions.append(
            GmFunction(
                header=func_header,
                bytecode=func_bytecode,
                debugNameStringOffset=func_debugNameStringOffset,
                baseClassNameOffset=func_baseClassNameOffset,
                lineInfoCount=func_lineInfoCount,
                lineInfo=func_lineInfo,
                symbolStringOffset=func_symbolStringOffset,
            )
        )

    assert fn_data == b"", "Not all data consumed"

    return GmLib(header, source, string_table, functions)


def print_bytecode(lib: GmLib, idx):
    f = lib.functions[idx]
    bc = f.bytecode

    i = 0
    while i < len(bc):
        opcode = int.from_bytes(bc[i : i + 4], "little")
        print(f"{i:04} {Bytecode(opcode).name}", end="")
        match opcode:
            case Bytecode.BC_BRA | Bytecode.BC_BRZ | Bytecode.BC_BRNZ | Bytecode.BC_BRZK | Bytecode.BC_BRNZK:
                print(f" ptr={int.from_bytes(bc[i+4:i+8], 'little'):04}", end="")
                i += 4
            case Bytecode.BC_FOREACH | Bytecode.BC_PUSHINT:
                print(f" {int.from_bytes(bc[i+4:i+8], 'little')}", end="")
                i += 4
            case Bytecode.BC_PUSHFP:
                print(f" {struct.unpack('<f', bc[i+4:i+8])[0]}", end="")
                i += 4
            case Bytecode.BC_CALL:
                print(f" params={int.from_bytes(bc[i+4:i+8], 'little')}", end="")
                i += 4
            case Bytecode.BC_GETLOCAL | Bytecode.BC_SETLOCAL:
                print(
                    f" {lib.stringTable[f.symbolStringOffset[int.from_bytes(bc[i+4:i+8], 'little')]]}",
                    end="",
                )
                i += 4
            case Bytecode.BC_GETDOT | Bytecode.BC_SETDOT | Bytecode.BC_GETTHIS | Bytecode.BC_SETTHIS | Bytecode.BC_GETGLOBAL | Bytecode.BC_SETGLOBAL | Bytecode.BC_PUSHSTR:
                print(
                    f" {lib.stringTable[int.from_bytes(bc[i+4:i+8], 'little')]}", end=""
                )
                i += 4
            case Bytecode.BC_PUSHFN:
                print(f" function_{int.from_bytes(bc[i+4:i+8], 'little')}", end="")
                i += 4
        print()
        i += 4


def merge_patch(gmlib, patchlib):
    strings1 = gmlib.stringTable.data.split(b"\0")
    strings2 = patchlib.stringTable.data.split(b"\0")

    newstr = b"\0".join(strings1 + strings2)

    # find conflicting functions
    merge_candidates = []
    named_map = {gmlib.stringTable[f.debugNameStringOffset]: f for f in gmlib.functions}
    for f in patchlib.functions:
        fname = patchlib.stringTable[f.debugNameStringOffset]
        if fname in named_map:
            print(f"Candidate: {f.header.id} {named_map[fname].header.id}")
            merge_candidates.append((named_map[fname], f))

    for o, p in merge_candidates:
        i = 0
        # update string offsets
        while i < len(p.bytecode):
            opcode = int.from_bytes(p.bytecode[i : i + 4], "little")
            match opcode:
                case Bytecode.BC_BRA | Bytecode.BC_BRZ | Bytecode.BC_BRNZ | Bytecode.BC_BRZK | Bytecode.BC_BRNZK | Bytecode.BC_FOREACH | Bytecode.BC_PUSHINT | Bytecode.BC_PUSHFP | Bytecode.BC_CALL | Bytecode.BC_PUSHFN:
                    i += 4
                case Bytecode.BC_GETLOCAL | Bytecode.BC_SETLOCAL:
                    symbol_idx = int.from_bytes(p.bytecode[i + 4 : i + 8], "little")
                    ostr = patchlib.stringTable[p.symbolStringOffset[symbol_idx]]
                    p.symbolStringOffset[symbol_idx] = newstr.index(
                        ostr.encode("ascii") + b"\0"
                    )
                    i += 4
                case Bytecode.BC_GETDOT | Bytecode.BC_SETDOT | Bytecode.BC_GETTHIS | Bytecode.BC_SETTHIS | Bytecode.BC_GETGLOBAL | Bytecode.BC_SETGLOBAL | Bytecode.BC_PUSHSTR:
                    str_id = int.from_bytes(p.bytecode[i + 4 : i + 8], "little")
                    ostr = patchlib.stringTable[str_id]
                    newbc = newstr.index(ostr.encode("ascii") + b"\0").to_bytes(
                        4, "little"
                    )
                    p.bytecode = p.bytecode[: i + 4] + newbc + p.bytecode[i + 8 :]
                    i += 4
            i += 4

        oid = o.header.id
        o.header = p.header
        o.header.id = oid

        o.bytecode = p.bytecode
        o.symbolStringOffset = p.symbolStringOffset
        o.lineInfo = p.lineInfo
        o.lineInfoCount = p.lineInfoCount

    gmlib.stringTable = GmStringTable(newstr)


def write_gm_lib(gmlib: GmLib):
    data = b""
    st_data = (
        int.to_bytes(len(gmlib.stringTable.data), 4, "little") + gmlib.stringTable.data
    )
    sc_bytes = gmlib.sourceCode.source
    sc_data = struct.pack("<II", len(sc_bytes), gmlib.sourceCode.flags) + sc_bytes
    fn_data = int.to_bytes(len(gmlib.functions), 4, "little")
    for f in gmlib.functions:
        fn_data += struct.pack("<4sIIIIIII", *(f.header.__dict__.values()))
        fn_data += f.bytecode
        fn_data += int.to_bytes(f.debugNameStringOffset, 4, "little")
        for base in f.baseClassNameOffset:
            fn_data += int.to_bytes(base, 4, "little")
        fn_data += int.to_bytes(f.lineInfoCount, 4, "little")
        for li in f.lineInfo:
            fn_data += struct.pack("<II", *(li.__dict__.values()))
        for sso in f.symbolStringOffset:
            fn_data += int.to_bytes(sso, 4, "little")
    data = struct.pack(
        "<4sIIII",
        gmlib.header.magic,
        gmlib.header.flags,
        20,
        20 + len(st_data),
        20 + len(st_data) + len(sc_data),
    )
    data += st_data + sc_data + fn_data
    return data
