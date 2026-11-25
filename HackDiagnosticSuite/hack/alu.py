"""16-bit Hack ALU, built from the six control bits exactly like ALU.hdl."""

MASK = 0xFFFF


def alu(x, y, zx, nx, zy, ny, f, no):
    """Return (out, zr, ng) for 16-bit inputs x and y."""
    if zx:
        x = 0
    if nx:
        x = ~x & MASK
    if zy:
        y = 0
    if ny:
        y = ~y & MASK
    out = (x + y) & MASK if f else (x & y)
    if no:
        out = ~out & MASK
    zr = 1 if out == 0 else 0
    ng = (out >> 15) & 1
    return out, zr, ng


def to_signed(v):
    """Interpret a 16-bit value as two's complement."""
    v &= MASK
    return v - 0x10000 if v & 0x8000 else v
