#!/usr/bin/env python3
"""Full lines scan cleanly but text is jumbled — so the coordinate mapping is
likely fine and the cause is elsewhere. This isolates it:

Phase A: a sparse 2D shape drawn pixel-by-pixel (box outline + an X). No font.
         Clean box with a clean X  -> individual-pixel mapping is correct, the
         panel does NOT need a custom mapper. The problem is the font/text.
         Scrambled -> there IS a 2D mapping quirk full lines couldn't show.

Phase B: text drawn with the LIBRARY's bundled font (not the project's 5x7.bdf).
         Readable here -> the project's fonts/5x7.bdf is the culprit; swap it.
         Jumbled here too -> DrawText/graphics issue.

Settings match the app (mux=0, row_addr=0, RBG). Blue-free colors.
"""

import os
import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

WIDTH, HEIGHT = 64, 32

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)

# --- Phase A: sparse 2D shape, pixel-by-pixel (no font) ---------------------
canvas = matrix.CreateFrameCanvas()
inset = 2
# box outline
for x in range(inset, WIDTH - inset):
    canvas.SetPixel(x, inset, 255, 0, 0)
    canvas.SetPixel(x, HEIGHT - 1 - inset, 255, 0, 0)
for y in range(inset, HEIGHT - inset):
    canvas.SetPixel(inset, y, 255, 0, 0)
    canvas.SetPixel(WIDTH - 1 - inset, y, 255, 0, 0)
# an X across the box (diagonals)
for i in range(HEIGHT):
    x_left = int(i * (WIDTH - 1) / (HEIGHT - 1))
    canvas.SetPixel(x_left, i, 0, 255, 0)
    canvas.SetPixel(WIDTH - 1 - x_left, i, 0, 255, 0)
canvas = matrix.SwapOnVSync(canvas)
print(">>> PHASE A: a red BOX outline with a green X through it. Clean? (12s)")
time.sleep(12)

# --- Phase B: text with the library's bundled font --------------------------
candidates = [
    "/home/hao/rpi-rgb-led-matrix/fonts/6x10.bdf",
    os.path.expanduser("~/rpi-rgb-led-matrix/fonts/6x10.bdf"),
    "/home/hao/rpi-rgb-led-matrix/fonts/5x7.bdf",
]
font_path = next((p for p in candidates if os.path.exists(p)), None)
if font_path is None:
    print("!! library font not found; checked:", candidates, file=sys.stderr)
else:
    font = graphics.Font()
    font.LoadFont(font_path)
    canvas = matrix.CreateFrameCanvas()
    graphics.DrawText(canvas, font, 1, 10, graphics.Color(255, 0, 0), "ABCD12")
    graphics.DrawText(canvas, font, 1, 26, graphics.Color(0, 255, 0), "wxyz89")
    canvas = matrix.SwapOnVSync(canvas)
    print(f">>> PHASE B: text via library font {font_path}")
    print("    'ABCD12' / 'wxyz89' — readable? (12s)")
    time.sleep(12)

matrix.Clear()
print("done")
