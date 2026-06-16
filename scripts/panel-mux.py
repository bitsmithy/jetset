#!/usr/bin/env python3
"""Draw a border + text under a given multiplexing value.

Solid fills render fine on this panel but sparse content (text, lines) garbles
— the signature of a pixel-mapping/multiplexing mismatch. This draws SPARSE
content so the right mapping is visually obvious. Sweep values with mux-sweep.sh.

Usage: panel-mux.py <multiplexing 0-17> [hold-seconds]
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

MULTIPLEXING = int(sys.argv[1]) if len(sys.argv) > 1 else 0
HOLD_SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
WIDTH, HEIGHT = 64, 32

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True
options.multiplexing = MULTIPLEXING

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

# 1px green border around the full panel edge.
for x in range(WIDTH):
    canvas.SetPixel(x, 0, 0, 80, 0)
    canvas.SetPixel(x, HEIGHT - 1, 0, 80, 0)
for y in range(HEIGHT):
    canvas.SetPixel(0, y, 0, 80, 0)
    canvas.SetPixel(WIDTH - 1, y, 0, 80, 0)

# Readable text spanning most of the width.
font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")
graphics.DrawText(canvas, font, 2, 14, graphics.Color(255, 255, 255), "AbCd12")

canvas = matrix.SwapOnVSync(canvas)
print(f"multiplexing={MULTIPLEXING}: clean rectangle border + readable 'AbCd12'?")
time.sleep(HOLD_SECONDS)
matrix.Clear()
