#!/usr/bin/env python3
"""Final check: render the app's 4-row text card, held static, at a stable
slowdown, in any color (including combination colors that exercise multiple
channels at once).

Uses the project's own fonts/5x7.bdf and the app's exact row positions. Run it
per color to confirm text renders reliably:
  - red / green        : single working channels
  - yellow / cyan / white / orange : combination colors (exercise the
    channel-collapse we saw with white->red)

Usage: probe-text.py [color] [gpio_slowdown] [hold-seconds]
       color: red green blue yellow cyan magenta white orange  (default red 5 15)
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "orange": (255, 140, 0),
    "dimwhite": (64, 64, 64),
    "dimyellow": (64, 64, 0),
}

NAME = sys.argv[1] if len(sys.argv) > 1 else "red"
SLOWDOWN = int(sys.argv[2]) if len(sys.argv) > 2 else 5
HOLD = int(sys.argv[3]) if len(sys.argv) > 3 else 15
R, G, B = COLORS.get(NAME, (255, 0, 0))
FONT_HEIGHT = 7

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = SLOWDOWN
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")  # the project's font, the app's actual path
color = graphics.Color(R, G, B)

# App layout: same y-positions as renderer.render_flight_card.
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 1 + 0, color, "UAL123")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 2 + 1, color, "IAH-LAX")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 3 + 2, color, "B738")
graphics.DrawText(canvas, font, 1, FONT_HEIGHT * 4 + 3, color, "35K ft")

matrix.SwapOnVSync(canvas)
print(f">>> color={NAME} slowdown={SLOWDOWN}: four rows held {HOLD}s")
print("    UAL123 / IAH-LAX / B738 / 35K ft — all four readable and stable?")
time.sleep(HOLD)
matrix.Clear()
