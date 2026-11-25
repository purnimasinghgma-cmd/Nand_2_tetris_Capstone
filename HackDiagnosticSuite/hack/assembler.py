"""Two-pass Hack assembler (.asm -> 16-bit binary strings)."""

COMP = {
    "0": "101010", "1": "111111", "-1": "111010", "D": "001100", "A": "110000",
    "!D": "001101", "!A": "110001", "-D": "001111", "-A": "110011",
    "D+1": "011111", "A+1": "110111", "D-1": "001110", "A-1": "110010",
    "D+A": "000010", "D-A": "010011", "A-D": "000111", "D&A": "000000",
    "D|A": "010101",
}
JUMP = {"": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}

PREDEFINED = {f"R{i}": i for i in range(16)}
PREDEFINED.update({"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
                   "SCREEN": 16384, "KBD": 24576})


class AssemblerError(Exception):
    pass


def _comp_bits(comp):
    a = "1" if "M" in comp else "0"
    key = comp.replace("M", "A")
    if key not in COMP:
        # allow commutative forms such as A+D or A&D
        for sep in "+&|":
            if sep in key:
                left, right = key.split(sep)
                key = right + sep + left
                break
    if key not in COMP:
        raise AssemblerError(f"unknown computation '{comp}'")
    return a + COMP[key]


def _dest_bits(dest):
    return "".join("1" if r in dest else "0" for r in "ADM")


def assemble_with_source(lines):
    """Return (binary_lines, source_lines) with one entry per instruction."""
    symbols = dict(PREDEFINED)
    code = []
    for raw in lines:
        line = raw.split("//")[0].replace(" ", "").replace("\t", "").strip()
        if not line:
            continue
        if line.startswith("("):
            symbols[line[1:-1]] = len(code)
        else:
            code.append(line)

    binary, nxt = [], 16
    for ins in code:
        if ins.startswith("@"):
            v = ins[1:]
            if not v.isdigit():
                if v not in symbols:
                    symbols[v] = nxt
                    nxt += 1
                v = symbols[v]
            binary.append(format(int(v), "016b"))
        else:
            dest, rest = ins.split("=", 1) if "=" in ins else ("", ins)
            comp, jmp = rest.split(";", 1) if ";" in rest else (rest, "")
            if jmp not in JUMP:
                raise AssemblerError(f"unknown jump '{jmp}'")
            binary.append("111" + _comp_bits(comp) + _dest_bits(dest) + JUMP[jmp])
    return binary, code


def assemble(lines):
    return assemble_with_source(lines)[0]
