"""Hack Computer Lab dashboard.

Run:  python3 dashboard.py      then open http://localhost:8000
Pure standard library: a small Python web server runs the Hack CPU simulator
and serves the dashboard page in web/index.html.
"""
import json
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import diagnostics
from hack import alu, assemble_with_source, jump_control, Computer
from hack.alu import to_signed
from hack.assembler import COMP
from hack.computer import SCREEN, KBD

ROOT = Path(__file__).parent
STUDENT = {"name": "Purnima Singh", "roll": "2501730358"}


# ---------------------------------------------------------------- Part C CPU
class Machine:
    """The live CPU that runs Box.asm in a background thread."""

    def __init__(self):
        self.lock = threading.Lock()
        self.speed = 5000            # instructions per second
        self.running = True
        self.reset()
        threading.Thread(target=self._loop, daemon=True).start()

    def reset(self):
        lines = (ROOT / "asm" / "Box.asm").read_text().splitlines()
        binary, source = assemble_with_source(lines)
        self.cpu = Computer(binary, source)

    def _loop(self):
        tick = 0.02
        while True:
            time.sleep(tick)
            with self.lock:
                if self.running:
                    for _ in range(max(1, int(self.speed * tick))):
                        self.cpu.step()

    def control(self, body):
        with self.lock:
            action = body.get("action")
            if action == "pause":
                self.running = False
            elif action == "run":
                self.running = True
            elif action == "step":
                self.running = False
                self.cpu.step()
            elif action == "reset":
                self.reset()
            if "speed" in body:
                self.speed = max(10, min(20000, int(body["speed"])))

    def set_key(self, code):
        with self.lock:
            self.cpu.set_key(int(code))

    def state(self):
        with self.lock:
            c = self.cpu
            ins = c.rom[c.pc] if c.pc < len(c.rom) else 0
            screen = {a - SCREEN: c.ram[a] for a in range(SCREEN, KBD) if c.ram[a]}

            def word(row, w):
                return SCREEN + row * 32 + w

            monitor = []
            for label, addr in [
                ("Row 40 End", word(40, 31)),
                ("Row 41, Word 0 • Box Start", word(41, 0)),
                ("Row 41, Word 1 • Box", word(41, 1)),
                ("Row 41, Word 2 • Outside", word(41, 2)),
                ("Row 60, Word 0 • Box", word(60, 0)),
                ("Row 60, Word 1 • Box End", word(60, 1)),
                ("Row 61, Word 0 • Below Box", word(61, 0)),
            ]:
                monitor.append({"label": label, "addr": addr,
                                "value": to_signed(c.ram[addr])})
            return {
                "pc": c.pc, "A": c.A, "D": to_signed(c.D),
                "kbd": c.ram[KBD], "rom_bin": format(ins, "016b"),
                "rom_src": c.source[c.pc] if c.pc < len(c.source) else "",
                "cycles": c.cycles, "running": self.running,
                "speed": self.speed, "screen": screen, "monitor": monitor,
            }


MACHINE = Machine()


# ------------------------------------------------------------ Part A and B
def api_alu(body):
    x = int(body.get("x", 0)) & 0xFFFF
    y = int(body.get("y", 0)) & 0xFFFF
    ctl = [int(b) for b in body.get("ctl", [0] * 6)]
    j = [int(b) for b in body.get("j", [0, 0, 0])]
    out, zr, ng = alu(x, y, *ctl)
    return {"out": to_signed(out), "bin": format(out, "016b"), "zr": zr, "ng": ng,
            "jump": jump_control(zr, ng, *j)}


def api_presets():
    return [{"name": k, "bits": [int(ch) for ch in v]} for k, v in COMP.items()]


def api_program(body):
    name = Path(body.get("program", "Trace.asm")).name
    lines = (ROOT / "asm" / name).read_text().splitlines()
    binary, source = assemble_with_source(lines)
    cpu = Computer(binary, source)
    for addr, val in (body.get("ram") or {}).items():
        cpu.ram[int(addr)] = int(val) & 0xFFFF
    rows = []
    for _ in range(500):
        t = cpu.step()
        if t is None:
            break
        mem = {a: to_signed(v) for a, v in enumerate(cpu.ram[:200]) if v}
        rows.append({"cycle": t["cycle"], "pc": t["pc"], "src": t["src"],
                     "bin": t["bin"], "A": t["A"], "D": to_signed(t["D"]),
                     "next_pc": t["next_pc"], "mem": mem})
        if cpu.is_halted(t):
            break
    return {"program": name, "rows": rows,
            "listing": [{"line": i, "src": s, "bin": b}
                        for i, (s, b) in enumerate(zip(source, binary))]}


def api_report():
    results = []
    for module in diagnostics.MODULES:
        ok, text = module()
        results.append({"name": module.__name__.replace("module_", ""),
                        "ok": ok, "text": text})
    return {"student": STUDENT, "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "results": results}


def report_markdown():
    rep = api_report()
    head = (f"# Hack Diagnostic Report\n\nName: {STUDENT['name']}  \n"
            f"Roll no: {STUDENT['roll']}  \nGenerated: {rep['time']}\n\n")
    summary = diagnostics.table(
        [(r["name"], "PASS" if r["ok"] else "FAIL") for r in rep["results"]],
        ["module", "result"])
    return head + "## Summary\n\n" + summary + "\n\n" + "\n\n".join(
        r["text"] for r in rep["results"]) + "\n"


# ------------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                page = (ROOT / "web" / "index.html").read_bytes()
                self._send(200, page, "text/html; charset=utf-8")
            elif path == "/api/info":
                self._send(200, STUDENT)
            elif path == "/api/state":
                self._send(200, MACHINE.state())
            elif path == "/api/presets":
                self._send(200, api_presets())
            elif path == "/api/report.md":
                self._send(200, report_markdown().encode(), "text/markdown",
                           {"Content-Disposition":
                            'attachment; filename="Hack_Diagnostic_Report.md"'})
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:                      # keep the server alive
            self._send(500, {"error": str(exc)})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            path = self.path.split("?")[0]
            if path == "/api/key":
                MACHINE.set_key(body.get("code", 0))
                self._send(200, {"ok": True})
            elif path == "/api/control":
                MACHINE.control(body)
                self._send(200, {"ok": True})
            elif path == "/api/alu":
                self._send(200, api_alu(body))
            elif path == "/api/program":
                self._send(200, api_program(body))
            elif path == "/api/report":
                self._send(200, api_report())
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:
            self._send(500, {"error": str(exc)})


def main():
    port = 8000
    while True:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
            if port > 8020:
                raise
    url = f"http://localhost:{port}"
    print(f"Dashboard running at {url}   (press Ctrl+C to stop)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
