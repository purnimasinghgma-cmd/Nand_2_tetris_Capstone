import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diagnostics import MODULES, load  # noqa: E402
from hack import assemble  # noqa: E402


class DiagnosticModules(unittest.TestCase):
    def test_every_module_passes(self):
        for module in MODULES:
            with self.subTest(module=module.__name__):
                ok, text = module()
                self.assertTrue(ok, text)


class AssemblerAndCpu(unittest.TestCase):
    def test_known_encodings(self):
        self.assertEqual(assemble(["@2", "D=A"]),
                         ["0000000000000010", "1110110000010000"])
        self.assertEqual(assemble(["0;JMP"]), ["1110101010000111"])
        self.assertEqual(assemble(["M=D+M"]), ["1111000010001000"])

    def test_labels_and_variables(self):
        code = assemble(["@i", "M=1", "(L)", "@L", "0;JMP", "@j"])
        self.assertEqual(code[0], format(16, "016b"))   # i -> 16
        self.assertEqual(code[2], format(2, "016b"))    # L  -> 2
        self.assertEqual(len(code), 5)                  # label emits no code
        self.assertEqual(code[4], format(17, "016b"))   # j -> 17

    def test_add_program(self):
        pc, _ = load("Trace.asm")
        pc.run()
        self.assertEqual((pc.D, pc.ram[0]), (5, 5))

    def test_m_write_uses_old_a(self):
        # AM=M+1 must store to the old A address
        pc, _ = load("Trace.asm")
        pc.rom = [int(b, 2) for b in assemble(["@10", "M=1", "@10", "AM=M+1"])]
        pc.source = [""] * 4
        for _ in range(4):
            pc.step()
        self.assertEqual(pc.ram[10], 2)
        self.assertEqual(pc.A, 2)


if __name__ == "__main__":
    unittest.main()
