"""Hack Diagnostic Suite.

Usage (from the project folder, or press F5 in VS Code):
    python main.py                       run every diagnostic module + write report
    python main.py run asm/Max.asm       assemble and run a program, show the trace
    python main.py run asm/Max.asm --ram 0=7 --ram 1=12 --cycles 50
    python main.py assemble asm/Trace.asm   write Trace.hack next to the .asm
"""
import argparse
import sys
from pathlib import Path

from hack import assemble_with_source, Computer
from hack.alu import to_signed
from diagnostics import MODULES, table

ROOT = Path(__file__).parent


def cmd_all(_args):
    parts, results = ["# Hack Diagnostic Suite Report\n"], []
    for module in MODULES:
        ok, text = module()
        results.append((module.__name__.replace("module_", ""), ok))
        parts.append(text + "\n")
    summary = table([(n, "PASS" if ok else "FAIL") for n, ok in results],
                    ["module", "result"])
    parts.insert(1, "## Summary\n\n" + summary + "\n")
    report = "\n".join(parts)
    out = ROOT / "report" / "Diagnostic_Report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport saved to {out}")
    return 0 if all(ok for _, ok in results) else 1


def cmd_assemble(args):
    src = Path(args.file)
    binary, _ = assemble_with_source(src.read_text().splitlines())
    out = src.with_suffix(".hack")
    out.write_text("\n".join(binary) + "\n")
    print(f"{len(binary)} instructions written to {out}")
    return 0


def cmd_run(args):
    binary, source = assemble_with_source(Path(args.file).read_text().splitlines())
    pc = Computer(binary, source)
    for item in args.ram or []:
        addr, val = item.split("=")
        pc.ram[int(addr)] = int(val) & 0xFFFF
    rows = []
    for _ in range(args.cycles):
        t = pc.step()
        if t is None:
            break
        rows.append((t["cycle"], t["pc"], t["src"], t["A"], t["D"], t["next_pc"]))
        if pc.is_halted(t):
            break
    print(table(rows, ["cycle", "PC", "instruction", "A", "D", "next PC"]))
    print("\nRAM[0..16] (non-zero):",
          {a: to_signed(v) for a, v in enumerate(pc.ram[:17]) if v})
    nz = {a: to_signed(v) for a, v in enumerate(pc.ram[:16384]) if v and a > 16}
    if nz:
        print("RAM above 16 (non-zero):", nz)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("all", help="run all diagnostics (default)")
    a = sub.add_parser("assemble", help="assemble .asm to .hack")
    a.add_argument("file")
    r = sub.add_parser("run", help="assemble and run a program")
    r.add_argument("file")
    r.add_argument("--cycles", type=int, default=200)
    r.add_argument("--ram", action="append", help="preload RAM, e.g. --ram 0=7")
    args = p.parse_args()
    handler = {"assemble": cmd_assemble, "run": cmd_run}.get(args.cmd, cmd_all)
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
