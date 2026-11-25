# Hack Diagnostic Suite Report

## Summary

| module | result |
|---|---|
| alu | PASS |
| jump | PASS |
| trace | PASS |
| max | PASS |
| io | PASS |
| overflow | PASS |
| assembler | PASS |

## Module 1: ALU

| comp | x | y | zx nx zy ny f no | out | zr | ng | expected | result |
|---|---|---|---|---|---|---|---|---|
| 0 | 7 | 9 | 101010 | 0 | 1 | 0 | 0 | PASS |
| 1 | 7 | 9 | 111111 | 1 | 0 | 0 | 1 | PASS |
| -1 | 7 | 9 | 111010 | -1 | 0 | 1 | -1 | PASS |
| x | 7 | 9 | 001100 | 7 | 0 | 0 | 7 | PASS |
| y | 7 | 9 | 110000 | 9 | 0 | 0 | 9 | PASS |
| x+y | 7 | 9 | 000010 | 16 | 0 | 0 | 16 | PASS |
| x-y | 7 | 9 | 010011 | -2 | 0 | 1 | -2 | PASS |
| y-x | 7 | 9 | 000111 | 2 | 0 | 0 | 2 | PASS |
| x&y | 12 | 10 | 000000 | 8 | 0 | 0 | 8 | PASS |
| x|y | 12 | 10 | 010101 | 14 | 0 | 0 | 14 | PASS |

## Module 2: Flags and jump logic

Checked all 24 combinations of ALU output (-5, 0, 5) and jump bits (j1=JLT, j2=JEQ, j3=JGT).

| ALU out | zr | ng | j1j2j3 | takeJump | expected | result |
|---|---|---|---|---|---|---|
| -5 | 0 | 1 | 000 | 0 | 0 | PASS |
| -5 | 0 | 1 | 001 | 0 | 0 | PASS |
| -5 | 0 | 1 | 010 | 0 | 0 | PASS |
| -5 | 0 | 1 | 011 | 0 | 0 | PASS |
| -5 | 0 | 1 | 100 | 1 | 1 | PASS |
| -5 | 0 | 1 | 101 | 1 | 1 | PASS |
| -5 | 0 | 1 | 110 | 1 | 1 | PASS |
| -5 | 0 | 1 | 111 | 1 | 1 | PASS |
| 0 | 1 | 0 | 000 | 0 | 0 | PASS |
| 0 | 1 | 0 | 001 | 0 | 0 | PASS |
| 0 | 1 | 0 | 010 | 1 | 1 | PASS |
| 0 | 1 | 0 | 011 | 1 | 1 | PASS |
| 0 | 1 | 0 | 100 | 0 | 0 | PASS |
| 0 | 1 | 0 | 101 | 0 | 0 | PASS |
| 0 | 1 | 0 | 110 | 1 | 1 | PASS |
| 0 | 1 | 0 | 111 | 1 | 1 | PASS |
| 5 | 0 | 0 | 000 | 0 | 0 | PASS |
| 5 | 0 | 0 | 001 | 1 | 1 | PASS |
| 5 | 0 | 0 | 010 | 0 | 0 | PASS |
| 5 | 0 | 0 | 011 | 1 | 1 | PASS |
| 5 | 0 | 0 | 100 | 0 | 0 | PASS |
| 5 | 0 | 0 | 101 | 1 | 1 | PASS |
| 5 | 0 | 0 | 110 | 0 | 0 | PASS |
| 5 | 0 | 0 | 111 | 1 | 1 | PASS |

## Module 3: Fetch-decode-execute trace (Trace.asm)

In Hack, fetch, decode and execute for one instruction all happen in a single clock cycle.

| cycle | PC | instruction | binary | A | D | RAM[0] | next PC |
|---|---|---|---|---|---|---|---|
| 1 | 0 | @2 | 0000000000000010 | 2 | 0 | 0 | 1 |
| 2 | 1 | D=A | 1110110000010000 | 2 | 2 | 0 | 2 |
| 3 | 2 | @3 | 0000000000000011 | 3 | 2 | 0 | 3 |
| 4 | 3 | D=D+A | 1110000010010000 | 3 | 5 | 0 | 4 |
| 5 | 4 | @0 | 0000000000000000 | 0 | 5 | 0 | 5 |
| 6 | 5 | M=D | 1110001100001000 | 0 | 5 | 5 | 6 |
| 7 | 6 | @END | 0000000000000110 | 6 | 5 | 5 | 7 |
| 8 | 7 | 0;JMP | 1110101010000111 | 6 | 5 | 5 | 6 |

- [PASS] D = 5 (expected 5)
- [PASS] RAM[0] = 5 (expected 5)

## Module 4: Max.asm program test

| RAM[0] | RAM[1] | RAM[2] | expected | cycles | result |
|---|---|---|---|---|---|
| 3 | 9 | 9 | 9 | 14 | PASS |
| 9 | 3 | 9 | 9 | 12 | PASS |
| 5 | 5 | 5 | 5 | 14 | PASS |
| -4 | 2 | 2 | 2 | 14 | PASS |
| 2 | -4 | 2 | 2 | 12 | PASS |
| -8 | -3 | -3 | -3 | 14 | PASS |

## Module 5: Memory-mapped I/O (KeyToScreen.asm)

Memory map: RAM 0-16383, SCREEN 16384-24575, KBD 24576.

| key set | RAM[24576] | RAM[16384] | result |
|---|---|---|---|
| 0 | 0 | 0 | PASS |
| 75 | 75 | 75 | PASS |
| 130 | 130 | 130 | PASS |
| 0 | 0 | 0 | PASS |

## Module 6: Buffer boundary (Overflow.asm)

RAM[100..102] is a 3-word buffer. Writing one word past the end changes the neighbouring variable at RAM[103]; Hack has no bounds checking.

| address | role | before overflow write | after |
|---|---|---|---|
| 100 | buffer[0] | 10 | 10 |
| 101 | buffer[1] | 20 | 20 |
| 102 | buffer[2] | 30 | 30 |
| 103 | neighbour variable | 99 | 0 |

- [PASS] RAM[103] changed from 99 to 0

## Module 7: Assembler output (Trace.hack)

| line | assembly | binary |
|---|---|---|
| 0 | @2 | 0000000000000010 |
| 1 | D=A | 1110110000010000 |
| 2 | @3 | 0000000000000011 |
| 3 | D=D+A | 1110000010010000 |
| 4 | @0 | 0000000000000000 |
| 5 | M=D | 1110001100001000 |
| 6 | @END | 0000000000000110 |
| 7 | 0;JMP | 1110101010000111 |

- [PASS] @2 -> 0000000000000010
- [PASS] D=A -> 1110110000010000
