"""Hack CPU + ROM + memory-mapped RAM/screen/keyboard.

One call to Computer.step() is one clock cycle: fetch, decode and execute
all happen together, like the HDL CPU with ROM32K and Memory.
"""
from .alu import alu, MASK, to_signed
from .jump import jump_control

SCREEN = 16384
KBD = 24576
RAM_SIZE = KBD + 1


class Computer:
    def __init__(self, binary_lines, source_lines=None):
        self.rom = [int(b, 2) for b in binary_lines]
        self.source = source_lines or [""] * len(self.rom)
        self.ram = [0] * RAM_SIZE
        self.A = 0
        self.D = 0
        self.pc = 0
        self.cycles = 0

    # ---- memory-mapped I/O -------------------------------------------
    def set_key(self, code):
        """Put a key code on the keyboard register (RAM[24576])."""
        self.ram[KBD] = code & MASK

    def screen_words(self):
        return {a: self.ram[a] for a in range(SCREEN, KBD) if self.ram[a]}

    # ---- execution ---------------------------------------------------
    def step(self):
        """Run one instruction and return a trace dict, or None past ROM end."""
        if self.pc >= len(self.rom):
            return None
        pc = self.pc
        ins = self.rom[pc]
        trace = {"cycle": self.cycles + 1, "pc": pc,
                 "src": self.source[pc], "bin": format(ins, "016b")}

        if not (ins >> 15) & 1:                      # A-instruction
            self.A = ins & 0x7FFF
            self.pc = pc + 1
            trace["jump"] = 0
        else:                                        # C-instruction
            a = (ins >> 12) & 1
            zx, nx, zy, ny, f, no = [(ins >> s) & 1 for s in (11, 10, 9, 8, 7, 6)]
            d1, d2, d3 = (ins >> 5) & 1, (ins >> 4) & 1, (ins >> 3) & 1
            j1, j2, j3 = (ins >> 2) & 1, (ins >> 1) & 1, ins & 1

            addr = self.A & 0x7FFF if self.A < RAM_SIZE else 0
            y = self.ram[addr] if a else self.A
            out, zr, ng = alu(self.D, y, zx, nx, zy, ny, f, no)

            # M is written at the OLD A address, so write memory first
            if d3 and addr < RAM_SIZE:
                self.ram[addr] = out
            if d2:
                self.D = out
            if d1:
                self.A = out

            jump = jump_control(zr, ng, j1, j2, j3)
            self.pc = (self.A if jump else pc + 1) & 0x7FFF
            trace.update(jump=jump, out=out, zr=zr, ng=ng)

        self.cycles += 1
        trace.update(A=self.A, D=self.D, next_pc=self.pc)
        return trace

    def is_halted(self, trace):
        """True for the (END) @END / 0;JMP idiom: jump back onto its own @ line."""
        if trace is None:
            return True
        return bool(trace["jump"]) and trace["next_pc"] == trace["pc"] - 1 \
            and trace["next_pc"] < len(self.rom) \
            and self.rom[trace["next_pc"]] == trace["next_pc"]

    def run(self, max_cycles=100000):
        """Run until the halt loop or max_cycles. Returns the list of traces."""
        traces = []
        for _ in range(max_cycles):
            t = self.step()
            if t is None:
                break
            traces.append(t)
            if self.is_halted(t):
                break
        return traces

    def signed_ram(self, addr):
        return to_signed(self.ram[addr])
