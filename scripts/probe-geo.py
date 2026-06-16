#!/usr/bin/env python3
"""Confirm geometry is correct (no mapper needed) using only the solid RED
channel at the stable gpio_slowdown. Draws a box outline + an X, all red, and
holds. If this is a clean, stable box-with-an-X, the panel's pixel mapping is
standard and the earlier 'jumble' was purely refresh instability + the panel's
dead/flaky green & blue channels.

Usage: probe-geo.py [gpio_slowdown] [hold-seconds]   (default 5 15)
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

WIDTH, HEIGHT = 64, 32
SLOWDOWN = int(sys.argv[1]) if len(sys.argv) > 1 else 5
HOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 15

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = SLOWDOWN
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

RED = (255, 0, 0)
inset = 2
for x in range(inset, WIDTH - inset):
    canvas.SetPixel(x, inset, *RED)
    canvas.SetPixel(x, HEIGHT - 1 - inset, *RED)
for y in range(inset, HEIGHT - inset):
    canvas.SetPixel(inset, y, *RED)
    canvas.SetPixel(WIDTH - 1 - inset, y, *RED)
for i in range(HEIGHT):
    x_left = int(i * (WIDTH - 1) / (HEIGHT - 1))
    canvas.SetPixel(x_left, i, *RED)
    canvas.SetPixel(WIDTH - 1 - x_left, i, *RED)

matrix.SwapOnVSync(canvas)
print(f">>> slowdown={SLOWDOWN}: a RED box with a RED X. Clean, stable, correct geometry?")
time.sleep(HOLD)
matrix.Clear()
