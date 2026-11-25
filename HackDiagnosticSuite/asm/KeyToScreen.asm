// Memory-mapped I/O: copy the keyboard register to the first screen word
(LOOP)
@KBD
D=M
@SCREEN
M=D
@LOOP
0;JMP
