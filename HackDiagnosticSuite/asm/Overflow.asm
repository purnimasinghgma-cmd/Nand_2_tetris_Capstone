// Buffer-boundary demo: buffer = RAM[100..102], RAM[103] is a neighbouring variable.
// Writing past the end of the buffer corrupts RAM[103] (99 -> 0).
// (Hack cannot do M=10 directly, so each constant goes through D.)
@10
D=A
@100
M=D
@20
D=A
@101
M=D
@30
D=A
@102
M=D
@99
D=A
@103
M=D
// "buffer[3] = 0" -- one element past the end of the buffer
@103
M=0
(END)
@END
0;JMP
