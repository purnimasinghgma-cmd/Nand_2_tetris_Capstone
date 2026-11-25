"""Jump logic from the ALU flags (same gates as JumpControl.hdl)."""


def jump_control(zr, ng, jlt, jeq, jgt):
    """Return 1 if the jump should be taken.

    zr/ng are the ALU flags; jlt/jeq/jgt are the j1, j2, j3 bits of the
    instruction (jump if out < 0, == 0, > 0).
    """
    pos = 1 - (zr | ng)          # Not(Or(zr, ng))
    lt = jlt & ng
    eq = jeq & zr
    gt = jgt & pos
    return lt | eq | gt
