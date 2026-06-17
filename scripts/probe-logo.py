#!/usr/bin/env python3
"""Probe whether airline logos render on the panel's top-right corner.

Phase 1 fills the logo box (the app's exact rect) solid red — confirms that
region of the (possibly faulty) panel is alive. Phase 2 draws a real logo
silhouette through the app's own render_logo, at its real position. So:

  - Phase 1 blank            -> that corner of the panel is dead (hardware).
  - Phase 1 red, Phase 2 blank -> the logo pipeline is at fault (software).
  - both visible             -> logos work; the issue is elsewhere.

Run on the Pi with the service stopped (only one process can own the GPIO):
  sudo systemctl stop jetset
  sudo -E env PATH="$PATH" uv run python scripts/probe-logo.py [airline] [hold]
  sudo systemctl start jetset
"""

import os
import sys
import time
from pathlib import Path

# Point the logo loader at the invoking user's cache before importing the app
# modules (LOGO_DIR is resolved at import time). Under sudo, Path.home() is
# /root, so prefer SUDO_USER's home where the logos were actually downloaded.
if "JETSET_LOGO_DIR" not in os.environ:
    sudo_user = os.environ.get("SUDO_USER")
    base = Path(f"/home/{sudo_user}") if sudo_user else Path.home()
    os.environ["JETSET_LOGO_DIR"] = str(base / ".cache" / "jetset" / "logos")

from rgbmatrix import RGBMatrix, RGBMatrixOptions  # noqa: E402

from jetset.display import LOGO_DIR  # noqa: E402
from jetset.renderer import (  # noqa: E402
    CANVAS_WIDTH,
    LOGO_HEIGHT,
    LOGO_WIDTH,
    _scaled_logo,
    render_logo,
)

AIRLINE = sys.argv[1] if len(sys.argv) > 1 else "UAL"
HOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 8

print(f"LOGO_DIR={LOGO_DIR}")

# Brightness histogram of what the current (luminance) render would draw.
_scaled = _scaled_logo(AIRLINE)
if _scaled is not None:
    buckets = {"1-63": 0, "64-127": 0, "128-191": 0, "192-255": 0}
    for _y in range(_scaled.size[1]):
        for _x in range(_scaled.size[0]):
            _r, _g, _b, _a = _scaled.getpixel((_x, _y))
            if _a == 0 or (_r, _g, _b) == (0, 0, 0):
                continue
            lum = round(0.299 * _r + 0.587 * _g + 0.114 * _b)
            key = ("1-63" if lum < 64 else "64-127" if lum < 128
                   else "128-191" if lum < 192 else "192-255")
            buckets[key] += 1
    print(f"{AIRLINE} luminance histogram (drawn px by red value): {buckets}")

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 5
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True
options.pwm_bits = 6  # match the service — this is what dims faint reds

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

box_left = CANVAS_WIDTH - LOGO_WIDTH

# Phase 1: solid red block over the logo box.
canvas.Clear()
for y in range(LOGO_HEIGHT):
    for x in range(LOGO_WIDTH):
        canvas.SetPixel(box_left + x, y, 255, 0, 0)
canvas = matrix.SwapOnVSync(canvas)
print(f">>> Phase 1: solid red block at x{box_left}-{box_left + LOGO_WIDTH - 1}, "
      f"y0-{LOGO_HEIGHT - 1} (holding {HOLD}s)")
print("    Solid red rectangle in the TOP-RIGHT corner?")
time.sleep(HOLD)

# Phase 2: the current render_logo (luminance-scaled red — the suspect).
flight = type("ProbeFlight", (), {"airline": AIRLINE})()
canvas.Clear()
render_logo(canvas, flight)
canvas = matrix.SwapOnVSync(canvas)
print(f">>> Phase 2: {AIRLINE} via current render_logo (luminance) (holding {HOLD}s)")
print("    Any logo shape? (suspected too dim to see)")
time.sleep(HOLD)

# Phase 3: proposed fix — luminance with a brightness FLOOR. Maps lum [0,255]
# onto [FLOOR,255], so dark logo colors lift above the panel's threshold while
# brighter pixels stay brighter (keeps the shape detail, unlike a flat fill).
FLOOR = 120
scaled = _scaled_logo(AIRLINE)
new_w, new_h = scaled.size
x_off = CANVAS_WIDTH - LOGO_WIDTH + (LOGO_WIDTH - new_w) // 2
y_off = (LOGO_HEIGHT - new_h) // 2
canvas.Clear()
for y in range(new_h):
    for x in range(new_w):
        _r, _g, _b, a = scaled.getpixel((x, y))
        if a == 0 or (_r, _g, _b) == (0, 0, 0):
            continue
        lum = round(0.299 * _r + 0.587 * _g + 0.114 * _b)
        red = FLOOR + round(lum * (255 - FLOOR) / 255)
        canvas.SetPixel(x_off + x, y_off + y, red, 0, 0)
canvas = matrix.SwapOnVSync(canvas)
print(f">>> Phase 3: {AIRLINE} luminance with floor={FLOOR} (holding {HOLD}s)")
print("    Bright AND keeps the logo's internal detail?")
time.sleep(HOLD)

matrix.Clear()
