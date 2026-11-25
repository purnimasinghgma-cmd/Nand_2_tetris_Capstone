"""Diagnostic modules. Each returns (passed, markdown_text)."""
import itertools
from pathlib import Path

from hack import alu, jump_control, assemble_with_source, Computer
from hack.alu import to_signed
from hack.computer import SCREEN, KBD

ASM_DIR = Path(__file__).parent / "asm"


def load(name, ram=None):
    lines = (ASM_DIR / name).read_text().splitlines()
    binary, source = assemble_with_source(lines)
    pc = Computer(binary, source)
    for addr, val in (ram or {}).items():
        pc.ram[addr] = val & 0xFFFF
    return pc, binary


def table(rows, header):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def check(label, ok):
    return f"- [{'PASS' if ok else 'FAIL'}] {label}"


# ---- Module 1: ALU -------------------------------------------------------
def module_alu():
    # (name, x, y, control bits zx nx zy ny f no, expected)
    cases = [
        ("0", 7, 9, (1, 0, 1, 0, 1, 0), 0),
        ("1", 7, 9, (1, 1, 1, 1, 1, 1), 1),
        ("-1", 7, 9, (1, 1, 1, 0, 1, 0), -1),
        ("x", 7, 9, (0, 0, 1, 1, 0, 0), 7),
        ("y", 7, 9, (1, 1, 0, 0, 0, 0), 9),
        ("x+y", 7, 9, (0, 0, 0, 0, 1, 0), 16),
        ("x-y", 7, 9, (0, 1, 0, 0, 1, 1), -2),
        ("y-x", 7, 9, (0, 0, 0, 1, 1, 1), 2),
        ("x&y", 12, 10, (0, 0, 0, 0, 0, 0), 8),
        ("x|y", 12, 10, (0, 1, 0, 1, 0, 1), 14),
    ]
    rows, ok = [], True
    for name, x, y, ctl, exp in cases:
        out, zr, ng = alu(x & 0xFFFF, y & 0xFFFF, *ctl)
        good = to_signed(out) == exp
        ok &= good
        rows.append((name, x, y, "".join(map(str, ctl)), to_signed(out), zr, ng,
                     exp, "PASS" if good else "FAIL"))
    txt = "## Module 1: ALU\n\n" + table(
        rows, ["comp", "x", "y", "zx nx zy ny f no", "out", "zr", "ng",
               "expected", "result"])
    return ok, txt


# ---- Module 2: flags and jumps ------------------------------------------
def module_jump():
    # reference: decide the jump from the signed ALU output and the jump bits
    rows, ok = [], True
    for out_val in (-5, 0, 5):
        zr, ng = int(out_val == 0), int(out_val < 0)
        for j1, j2, j3 in itertools.product((0, 1), repeat=3):
            expected = int((j1 and out_val < 0) or (j2 and out_val == 0)
                           or (j3 and out_val > 0))
            got = jump_control(zr, ng, j1, j2, j3)
            ok &= got == expected
            rows.append((out_val, zr, ng, f"{j1}{j2}{j3}", got, expected,
                         "PASS" if got == expected else "FAIL"))
    txt = ("## Module 2: Flags and jump logic\n\n"
           "Checked all 24 combinations of ALU output (-5, 0, 5) and jump bits "
           "(j1=JLT, j2=JEQ, j3=JGT).\n\n"
           + table(rows, ["ALU out", "zr", "ng", "j1j2j3", "takeJump",
                          "expected", "result"]))
    return ok, txt


# ---- Module 3: FDE trace -------------------------------------------------
def module_trace():
    pc, binary = load("Trace.asm")
    rows = []
    while True:
        t = pc.step()
        rows.append((t["cycle"], t["pc"], t["src"], t["bin"], t["A"], t["D"],
                     pc.ram[0], t["next_pc"]))
        if pc.is_halted(t) or t["cycle"] >= 50:
            break
    ok = pc.D == 5 and pc.ram[0] == 5
    txt = ("## Module 3: Fetch-decode-execute trace (Trace.asm)\n\n"
           "In Hack, fetch, decode and execute for one instruction all "
           "happen in a single clock cycle.\n\n"
           + table(rows, ["cycle", "PC", "instruction", "binary", "A", "D",
                          "RAM[0]", "next PC"])
           + "\n\n" + check(f"D = {pc.D} (expected 5)", pc.D == 5)
           + "\n" + check(f"RAM[0] = {pc.ram[0]} (expected 5)", pc.ram[0] == 5))
    return ok, txt


# ---- Module 4: programs (Max) -------------------------------------------
def module_max():
    rows, ok = [], True
    for a, b in [(3, 9), (9, 3), (5, 5), (-4, 2), (2, -4), (-8, -3)]:
        pc, _ = load("Max.asm", {0: a, 1: b})
        pc.run(1000)
        got = to_signed(pc.ram[2])
        exp = max(a, b)
        ok &= got == exp
        rows.append((a, b, got, exp, pc.cycles, "PASS" if got == exp else "FAIL"))
    txt = "## Module 4: Max.asm program test\n\n" + table(
        rows, ["RAM[0]", "RAM[1]", "RAM[2]", "expected", "cycles", "result"])
    return ok, txt


# ---- Module 5: memory-mapped I/O ----------------------------------------
def module_io():
    pc, _ = load("KeyToScreen.asm")
    rows, ok = [], True
    for key in (0, 75, 130, 0):          # none, 'K', left arrow, released
        pc.set_key(key)
        for _ in range(8):
            pc.step()
        got = pc.ram[SCREEN]
        ok &= got == key
        rows.append((key, pc.ram[KBD], got, "PASS" if got == key else "FAIL"))
    txt = ("## Module 5: Memory-mapped I/O (KeyToScreen.asm)\n\n"
           f"Memory map: RAM 0-16383, SCREEN {SCREEN}-{KBD - 1}, KBD {KBD}.\n\n"
           + table(rows, ["key set", f"RAM[{KBD}]", f"RAM[{SCREEN}]", "result"]))
    return ok, txt


# ---- Module 6: buffer boundary ------------------------------------------
def module_overflow():
    pc, _ = load("Overflow.asm")
    before = None
    while True:
        snap = [pc.ram[a] for a in range(100, 104)]
        t = pc.step()
        if t["src"] == "M=0":            # the out-of-bounds write
            before = snap
        if pc.is_halted(t) or t["cycle"] >= 100:
            break
    after = [pc.ram[a] for a in range(100, 104)]
    ok = before == [10, 20, 30, 99] and after == [10, 20, 30, 0]
    rows = [(a, f"buffer[{a - 100}]" if a < 103 else "neighbour variable",
             before[a - 100], after[a - 100]) for a in range(100, 104)]
    txt = ("## Module 6: Buffer boundary (Overflow.asm)\n\n"
           "RAM[100..102] is a 3-word buffer. Writing one word past the end "
           "changes the neighbouring variable at RAM[103]; Hack has no "
           "bounds checking.\n\n"
           + table(rows, ["address", "role", "before overflow write", "after"])
           + "\n\n" + check("RAM[103] changed from 99 to 0", ok))
    return ok, txt


# ---- Module 7: assembler -------------------------------------------------
def module_assembler():
    _, binary = load("Trace.asm")
    expect = ["0000000000000010", "1110110000010000"]
    ok = binary[:2] == expect
    rows = [(i, s, b) for i, (s, b) in enumerate(zip(load("Trace.asm")[0].source,
                                                      binary))]
    txt = ("## Module 7: Assembler output (Trace.hack)\n\n"
           + table(rows, ["line", "assembly", "binary"])
           + "\n\n" + check("@2 -> 0000000000000010", binary[0] == expect[0])
           + "\n" + check("D=A -> 1110110000010000", binary[1] == expect[1]))
    return ok, txt


MODULES = [module_alu, module_jump, module_trace, module_max, module_io,
           module_overflow, module_assembler]
