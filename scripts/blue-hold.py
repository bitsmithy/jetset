#!/usr/bin/env python3
"""Hold a sustained, full-brightness BLUE fill to test the blue connection.

Blue flashes briefly at matrix init but won't hold during a steady fill — the
signature of an intermittent connection. While this runs, GENTLY press/wiggle
the IDC ribbon cable at BOTH ends (HAT and panel):

  - blue flickers on/off in response to pressure  -> bad connection (reseat /
    replace the ribbon cable, or try the panel's other HUB75 header)
  - blue stays solid for the full 30s            -> connection is fine; the
    earlier blanks were the dim 150-level drive, not a fault
  - blue stays totally dark regardless           -> deeper fault on that line

Uses led_rgb_sequence=RBG (this panel's order) so logical blue drives the
physical blue subpixels.
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
canvas = matrix.CreateFrameCanvas()
canvas.Fill(0, 0, 255)  # full-brightness blue
matrix.SwapOnVSync(canvas)

print("Solid BLUE for 30s — gently wiggle the ribbon cable at both ends and watch.")
time.sleep(30)
matrix.Clear()
print("done")
