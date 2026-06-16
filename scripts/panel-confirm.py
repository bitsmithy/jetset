#!/usr/bin/env python3
"""Confirm a (multiplexing, rows, cols) combo renders the app's 4-row card.

Mirrors renderer.render_flight_card exactly (same y-positions, colors, font) so
we verify the actual use case before baking the values into config. For a
multiplexed 1/16-scan panel the PHYSICAL rows/cols differ from the visible
64x32 — the mux mapper folds e.g. 16x128 physical into 32x64 visible.

Usage: panel-confirm.py [multiplexing] [rows] [cols]   (default: 17 16 128)
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

MULTIPLEXING = int(sys.argv[1]) if len(sys.argv) > 1 else 17
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 16
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 128
FONT_HEIGHT = 7

options = RGBMatrixOptions()
options.cols = COLS
options.rows = ROWS
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True
options.multiplexing = MULTIPLEXING

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")

# Same layout as renderer.render_flight_card.
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 1 + 0, graphics.Color(255, 140, 0), "UAL123")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 2 + 1, graphics.Color(0, 255, 255), "IAH->LAX")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 3 + 2, graphics.Color(0, 255, 0), "B738")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 4 + 3, graphics.Color(0, 120, 255), "35K ft")

canvas = matrix.SwapOnVSync(canvas)
print(f"mux={MULTIPLEXING} rows={ROWS} cols={COLS}: 4 rows, distinct colors (orange/cyan/green/blue)?")
time.sleep(15)
matrix.Clear()
