#!/usr/bin/env python3
"""Test each color channel with a solid full-panel fill.

A solid fill is immune to pixel-mapping/multiplexing scrambles, so this
isolates the color channels themselves. If solid GREEN or BLUE does NOT light
the whole panel in that color, that channel isn't reaching the panel.

Whether that's a config or a hardware fault depends on the knobs below, so they
are all overridable — a "dead" channel at the wrong gpio_slowdown (signal
timing) or without a required panel_type init is a config issue, not the panel:

  panel-colors.py [gpio_slowdown] [rgb_sequence] [panel_type]
  defaults:        5               RGB            (none)

  gpio_slowdown : 5 is required on the Pi 3 A+ / Adafruit HAT; 4 is unstable and
                  can drop or garble a channel (masquerades as a dead channel).
  rgb_sequence  : RGB GRB RBG ... — only PERMUTES colors, never blanks one.
  panel_type    : "" or FM6126A — some panels need the FM6126A init or come up
                  with wrong/missing channels.
"""

import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

SLOWDOWN = int(sys.argv[1]) if len(sys.argv) > 1 else 5
RGB_SEQUENCE = sys.argv[2] if len(sys.argv) > 2 else "RGB"
PANEL_TYPE = sys.argv[3] if len(sys.argv) > 3 else ""

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = SLOWDOWN
options.led_rgb_sequence = RGB_SEQUENCE
options.panel_type = PANEL_TYPE
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)
print(f">>> gpio_slowdown={SLOWDOWN} rgb_sequence={RGB_SEQUENCE} "
      f"panel_type={PANEL_TYPE or '(none)'}")

for name, (r, g, b) in [
    ("RED", (150, 0, 0)),
    ("GREEN", (0, 150, 0)),
    ("BLUE", (0, 0, 150)),
    ("WHITE", (150, 150, 150)),
]:
    canvas = matrix.CreateFrameCanvas()
    canvas.Fill(r, g, b)
    matrix.SwapOnVSync(canvas)
    print(f">>> solid {name} — the ENTIRE panel should be {name}")
    time.sleep(4)

matrix.Clear()
print("done")
