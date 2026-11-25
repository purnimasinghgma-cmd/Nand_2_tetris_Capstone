// Part C: keyboard polling box.
// While any key is held (RAM[24576] != 0) draw a black box (-1) in screen rows 41..60,
// words 0..1 (32 pixels wide). When no key is held, erase it (0).
// Row 41, word 0 = 16384 + 41*32 = 17696
(LOOP)
@KBD
D=M
@DRAW
D;JNE
@color
M=0
@FILL
0;JMP
(DRAW)
@color
M=-1
(FILL)
@17696
D=A
@addr
M=D
@20
D=A
@rows
M=D
(ROWLOOP)
@color
D=M
@addr
A=M
M=D
A=A+1
M=D
@32
D=A
@addr
M=D+M
@rows
MD=M-1
@ROWLOOP
D;JGT
@LOOP
0;JMP
