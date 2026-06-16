#!/usr/bin/env python3
"""Show solid RED/GREEN/BLUE under a given led_rgb_sequence.

Solid-color fills tested earlier came out misordered (blue-input lit green) and
partly blank. led_rgb_sequence permutes the panel's subpixel order. The correct
sequence makes red->red, green->green, blue->blue. If BLUE never appears under
ANY of the six sequences, the blue channel is a hardware fault, not config.

Usage: panel-rgbseq.py <SEQUENCE>   one of RGB RBG GRB GBR BRG BGR
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

SEQUENCE = sys.argv[1] if len(sys.argv) > 1 else "RGB"

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True
options.led_rgb_sequence = SEQUENCE

matrix = RGBMatrix(options=options)

for name, (r, g, b) in [("RED", (150, 0, 0)), ("GREEN", (0, 150, 0)), ("BLUE", (0, 0, 150))]:
    canvas = matrix.CreateFrameCanvas()
    canvas.Fill(r, g, b)
    matrix.SwapOnVSync(canvas)
    print(f"  seq={SEQUENCE}: solid {name} — panel should be {name}")
    time.sleep(2.5)

matrix.Clear()
