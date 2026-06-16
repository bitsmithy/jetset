#!/usr/bin/env python3
"""Distinguish a power/current problem from a data problem on the blue channel.

Blue and white fail while red/green work — the signature of a sagging 5V rail
(blue LEDs have the highest forward voltage, so they drop out first under
brownout; white is peak current). This draws a SMALL blue patch (tiny current)
then a FULL-panel blue fill (large current):

  - small blue lights, full blue blank/dim  -> POWER: the 5V rail sags under
    load. Check the panel's power feed (supply rating, barrel jack, screw
    terminal, wire gauge). Ideally measure 5V at the panel input during the
    full-blue phase — if it sags below ~4.5V, that's the cause.
  - both blank                              -> not current; deeper blue fault
  - both solid blue                         -> blue is fine at this drive

Uses led_rgb_sequence=RBG (this panel's order).
"""

import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True
options.led_rgb_sequence = "RBG"

matrix = RGBMatrix(options=options)

# Phase 1: small 8x8 blue patch in the center — minimal current.
canvas = matrix.CreateFrameCanvas()
for x in range(28, 36):
    for y in range(12, 20):
        canvas.SetPixel(x, y, 0, 0, 255)
matrix.SwapOnVSync(canvas)
print(">>> SMALL blue patch (low current) — does this 8x8 center square light blue? (12s)")
time.sleep(12)

# Phase 2: full-panel blue — large current.
canvas = matrix.CreateFrameCanvas()
canvas.Fill(0, 0, 255)
matrix.SwapOnVSync(canvas)
print(">>> FULL-PANEL blue (high current) — measure 5V at the panel now if you can. (12s)")
time.sleep(12)

matrix.Clear()
print("done")
