#!/usr/bin/env python3
"""Reverse-engineer probe: animate ONE logical line scanning the panel to reveal
how logical coordinates map to physical pixels on this non-standard panel.

Phase 1: a full-width RED horizontal line steps through logical rows 0..31.
Phase 2: a full-height GREEN vertical line steps through logical cols 0..63.

Watch how the PHYSICAL line moves and describe the motion:
  - smooth top->bottom / left->right       -> that axis maps linearly
  - jumps between halves, or two lines at   -> reveals the scan/multiplex split
    once moving together, or scans in blocks
Blue-free colors so the dead blue channel doesn't interfere. Runs each phase
twice so you can confirm the pattern.
"""

import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

WIDTH, HEIGHT = 64, 32

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

for _ in range(2):
    print("PHASE 1: RED horizontal line, logical row 0 -> 31 (top to bottom)")
    for y in range(HEIGHT):
        canvas.Clear()
        for x in range(WIDTH):
            canvas.SetPixel(x, y, 255, 0, 0)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(0.4)

time.sleep(1.0)

for _ in range(2):
    print("PHASE 2: GREEN vertical line, logical col 0 -> 63 (left to right)")
    for x in range(WIDTH):
        canvas.Clear()
        for y in range(HEIGHT):
            canvas.SetPixel(x, y, 0, 255, 0)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(0.25)

matrix.Clear()
print("done")
