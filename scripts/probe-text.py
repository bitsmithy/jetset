#!/usr/bin/env python3
"""Render the app's 4-row text card, held static, in any colour — a quick check
that text and combination colours render cleanly on the panel.

Uses the project's own fonts/5x7.bdf and the app's exact row positions.

Usage: probe-text.py [color] [hold-seconds]
       color: red green blue yellow cyan magenta white orange  (default red, 15s)
"""

import sys
import time

from jetset.backend import build_matrix, graphics

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
HOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 15
R, G, B = COLORS.get(NAME, (255, 0, 0))
FONT_HEIGHT = 7

matrix = build_matrix()
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
print(f">>> color={NAME}: four rows held {HOLD}s")
print("    UAL123 / IAH-LAX / B738 / 35K ft — all four readable and stable?")
time.sleep(HOLD)
matrix.Clear()
