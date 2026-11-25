# Hack Diagnostic Suite

A Python version of the Nand2Tetris Hack computer: ALU, jump logic, CPU,
memory-mapped I/O and a two-pass assembler, plus diagnostic programs.
Needs only Python 3.9+ (no packages, no Java simulator).

## Dashboard website (Part A / B / C / Submission)
```
python3 dashboard.py
```
Opens http://localhost:8000 in your browser. The page shows the student name and
roll number, and every calculation runs in Python on the server. Part C: hold any
key (or the HOLD KEY button) to draw the box. Stop the server with Ctrl+C.

## Run in VS Code
1. File > Open Folder > `HackDiagnosticSuite`.
2. Install the **Python** extension.
3. Open `main.py` and press **F5** (choose "Run all diagnostics"),
   or in the terminal: `python main.py`.

Other launch options (Run and Debug dropdown): "Run current .asm file"
(open any file in `asm/` first) and "Run unit tests".

## Commands
```
python main.py                          all 7 diagnostic modules + report
python main.py run asm/Max.asm --ram 0=7 --ram 1=12
python main.py run asm/Trace.asm --cycles 20
python main.py assemble asm/Trace.asm   writes asm/Trace.hack
python -m unittest discover -s tests -v
```
`python main.py` saves `report/Diagnostic_Report.md` with every table
(ALU, jump logic, FDE trace, Max, I/O, buffer boundary, assembler).

## Layout
- `hack/` ALU, jump logic, assembler, CPU + memory (the simulator)
- `asm/` Trace, Max, KeyToScreen, Overflow programs
- `hdl/` CPU.hdl and JumpControl.hdl for the real Hardware Simulator
- `dashboard.py` + `web/index.html` the website dashboard
- `diagnostics.py`, `main.py`, `tests/`

Note: Hack cannot write a constant straight to memory (`M=10` is invalid);
load it into D first, as `asm/Overflow.asm` does.
