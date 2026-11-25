// FDE trace: D = 2 + 3, then store in RAM[0]. Expected: D = 5, RAM[0] = 5
@2
D=A
@3
D=D+A
@0
M=D
(END)
@END
0;JMP
