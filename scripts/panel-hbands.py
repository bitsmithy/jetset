#!/usr/bin/env python3
"""Characterize the horizontal column mapping.

At mux=0/rows=32/cols=64 the vertical layout is correct but columns are
scrambled. Draw known patterns so we can read off the exact column permutation
and choose the right pixel mapper / fix.

Usage: panel-hbands.py [multiplexing] [rows] [cols]   (default 0 32 64)
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

MUX = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 32
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 64

options = RGBMatrixOptions()
options.cols = COLS
options.rows = ROWS
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True
options.multiplexing = MUX

matrix = RGBMatrix(options=options)


def show(label, paint, seconds=10):
    canvas = matrix.CreateFrameCanvas()
    w, h = canvas.width, canvas.height
    for x in range(w):
        for y in range(h):
            r, g, b = paint(x, w)
            canvas.SetPixel(x, y, r, g, b)
    matrix.SwapOnVSync(canvas)
    print(f">>> {label}  ({seconds}s)")
    time.sleep(seconds)


# Pattern A: four equal quarters, left->right RED GREEN BLUE WHITE.
QUARTERS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
show(
    "A: quarters L->R should be RED GREEN BLUE WHITE",
    lambda x, w: QUARTERS[min(x // (w // 4), 3)],
)

# Pattern B: even columns RED, odd columns BLUE — exposes odd/even interleave.
# If columns are interleaved you'll see a RED block and a BLUE block (or larger
# stripes) instead of a fine red/blue comb.
show(
    "B: even cols RED, odd cols BLUE (fine comb if mapping is linear)",
    lambda x, w: (255, 0, 0) if x % 2 == 0 else (0, 0, 255),
    8,
)

matrix.Clear()
print("done")
