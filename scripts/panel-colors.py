#!/usr/bin/env python3
"""Test each colour channel with a solid full-panel fill.

A solid fill is immune to pixel-mapping scrambles, so this isolates the colour
channels themselves: if solid GREEN or BLUE doesn't light the whole panel in
that colour, that channel isn't reaching the panel — check the panel's power
feed (the ribbon carries data + ground only, so the panel needs 5V on its own
header) and the HAT.
"""

import time

from jetset.backend import build_matrix

matrix = build_matrix()

for name, (r, g, b) in [
    ("RED", (150, 0, 0)),
    ("GREEN", (0, 150, 0)),
    ("BLUE", (0, 0, 150)),
    ("WHITE", (150, 150, 150)),
]:
    canvas = matrix.CreateFrameCanvas()
    canvas.Fill(r, g, b)
    matrix.SwapOnVSync(canvas)
    print(f">>> solid {name} — the ENTIRE panel should be {name}")
    time.sleep(4)

matrix.Clear()
print("done")
