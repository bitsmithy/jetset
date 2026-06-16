#!/usr/bin/env python3
"""Test each color channel with a solid full-panel fill.

A solid fill is immune to pixel-mapping/multiplexing scrambles, so this
isolates the color channels themselves. If solid GREEN or BLUE does NOT light
the whole panel in that color, that channel isn't reaching the panel — a
hardware/wiring fault (ribbon cable, HAT seating, solder), not a config issue.
"""

import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)

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
