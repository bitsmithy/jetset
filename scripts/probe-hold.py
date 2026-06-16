#!/usr/bin/env python3
"""Hold a STATIC box+X and see if it stays stable or degrades.

The image renders correctly then corrupts under sustained refresh — a
refresh-stability / GPIO-timing symptom. This redraws nothing after the first
frame, so any degradation is the hardware refresh, not the code. Sweep
gpio_slowdown (and optionally hardware-pulsing) to see if any setting holds the
image steady for the full duration.

Usage: probe-hold.py [gpio_slowdown] [disable_hw_pulsing 0|1] [hold-seconds]
       defaults: 4 1 12
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

WIDTH, HEIGHT = 64, 32

SLOWDOWN = int(sys.argv[1]) if len(sys.argv) > 1 else 4
DISABLE_PULSING = (int(sys.argv[2]) if len(sys.argv) > 2 else 1) == 1
HOLD = int(sys.argv[3]) if len(sys.argv) > 3 else 12

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = SLOWDOWN
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = DISABLE_PULSING

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

inset = 2
for x in range(inset, WIDTH - inset):
    canvas.SetPixel(x, inset, 255, 0, 0)
    canvas.SetPixel(x, HEIGHT - 1 - inset, 255, 0, 0)
for y in range(inset, HEIGHT - inset):
    canvas.SetPixel(inset, y, 255, 0, 0)
    canvas.SetPixel(WIDTH - 1 - inset, y, 255, 0, 0)
for i in range(HEIGHT):
    x_left = int(i * (WIDTH - 1) / (HEIGHT - 1))
    canvas.SetPixel(x_left, i, 0, 255, 0)
    canvas.SetPixel(WIDTH - 1 - x_left, i, 0, 255, 0)

matrix.SwapOnVSync(canvas)
print(f">>> slowdown={SLOWDOWN} disable_pulsing={DISABLE_PULSING}: "
      f"does the box+X stay STABLE for {HOLD}s, or degrade?")
time.sleep(HOLD)
matrix.Clear()
