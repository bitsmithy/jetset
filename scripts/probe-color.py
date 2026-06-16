#!/usr/bin/env python3
"""Compare animated vs static rendering for a single color, at a stable slowdown.

Green worked as a sweeping line but vanished as a static X — but those tests
differed in slowdown (4 vs 5) AND animated-vs-static AND had a red box next to
the green. This isolates it: pick ONE color, run the SAME three things at the
SAME slowdown:

  Phase 1: horizontal line sweep (animated)
  Phase 2: vertical line sweep (animated)
  Phase 3: static box + X, held

Run it per color (e.g. 'green 5' then 'red 5') and compare: does the color show
in the animated sweeps but disappear in the static shape? That would pin a
static-content problem to that specific channel.

Usage: probe-color.py [color] [gpio_slowdown]
       color: red green blue yellow cyan white magenta   (default green 5)
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "white": (255, 255, 255),
    "magenta": (255, 0, 255),
}

NAME = sys.argv[1] if len(sys.argv) > 1 else "green"
SLOWDOWN = int(sys.argv[2]) if len(sys.argv) > 2 else 5
R, G, B = COLORS.get(NAME, (0, 255, 0))
WIDTH, HEIGHT = 64, 32

options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = SLOWDOWN
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

print(f">>> color={NAME} slowdown={SLOWDOWN}")

print("    PHASE 1: horizontal line sweep (animated)")
for y in range(HEIGHT):
    canvas.Clear()
    for x in range(WIDTH):
        canvas.SetPixel(x, y, R, G, B)
    canvas = matrix.SwapOnVSync(canvas)
    time.sleep(0.3)

print("    PHASE 2: vertical line sweep (animated)")
for x in range(WIDTH):
    canvas.Clear()
    for y in range(HEIGHT):
        canvas.SetPixel(x, y, R, G, B)
    canvas = matrix.SwapOnVSync(canvas)
    time.sleep(0.2)

print("    PHASE 3: STATIC box + X (held 12s) — does it show as cleanly as the sweeps?")
canvas.Clear()
inset = 2
for x in range(inset, WIDTH - inset):
    canvas.SetPixel(x, inset, R, G, B)
    canvas.SetPixel(x, HEIGHT - 1 - inset, R, G, B)
for y in range(inset, HEIGHT - inset):
    canvas.SetPixel(inset, y, R, G, B)
    canvas.SetPixel(WIDTH - 1 - inset, y, R, G, B)
for i in range(HEIGHT):
    x_left = int(i * (WIDTH - 1) / (HEIGHT - 1))
    canvas.SetPixel(x_left, i, R, G, B)
    canvas.SetPixel(WIDTH - 1 - x_left, i, R, G, B)
canvas = matrix.SwapOnVSync(canvas)
time.sleep(12)

matrix.Clear()
print("done")
