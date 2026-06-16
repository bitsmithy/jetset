#!/usr/bin/env python3
"""Verify the app's content renders correctly, ignoring the dead blue channel.

Draws renderer.render_flight_card's exact 4-row layout in BLUE-FREE colors
(red / green / yellow / orange), so we judge readability and positioning
without the blue fault interfering. Sweeps row_address_type x multiplexing —
per hzeller issue #1640, 1/16-scan panels often need row_address_type=3 (and
sometimes a multiplexing mapper) to stop the jumble.

Usage: panel-content.py [row_addr_type] [multiplexing] [hold-seconds]
       defaults: 0 0 15
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

ROW_ADDR_TYPE = int(sys.argv[1]) if len(sys.argv) > 1 else 0
MULTIPLEXING = int(sys.argv[2]) if len(sys.argv) > 2 else 0
HOLD_SECONDS = int(sys.argv[3]) if len(sys.argv) > 3 else 15
FONT_HEIGHT = 7

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.multiplexing = MULTIPLEXING
options.row_address_type = ROW_ADDR_TYPE
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")

# Same positions as render_flight_card, blue-free colors (B=0 everywhere).
RED = graphics.Color(255, 0, 0)
GREEN = graphics.Color(0, 255, 0)
YELLOW = graphics.Color(255, 255, 0)
ORANGE = graphics.Color(255, 90, 0)

graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 1 + 0, RED, "UAL123")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 2 + 1, GREEN, "IAH-LAX")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 3 + 2, YELLOW, "B738")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 4 + 3, ORANGE, "35K ft")

matrix.SwapOnVSync(canvas)
print(f"row_addr_type={ROW_ADDR_TYPE} multiplexing={MULTIPLEXING}: "
      "UAL123 / IAH-LAX / B738 / 35K ft")
print("All four readable, in order, no scrambling within each row?")
time.sleep(HOLD_SECONDS)
matrix.Clear()
