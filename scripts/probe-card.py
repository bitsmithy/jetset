#!/usr/bin/env python3
"""Confirm the privilege-drop fix on hardware: render the real full card
(text + render_logo) with drop_privileges=False, so the logo — loaded lazily in
the render path — can still be read after the matrix initializes. Cycles the 4
metric pages so you can confirm the logo shows AND the text stays clean.

Run on the Pi with the service stopped:
  sudo systemctl stop jetset
  sudo -E env PATH="$PATH" uv run python scripts/probe-card.py [airline]
  sudo systemctl start jetset
"""

import os
import sys
import time
from pathlib import Path

if "JETSET_LOGO_DIR" not in os.environ:
    sudo_user = os.environ.get("SUDO_USER")
    base = Path(f"/home/{sudo_user}") if sudo_user else Path.home()
    os.environ["JETSET_LOGO_DIR"] = str(base / ".cache" / "jetset" / "logos")

from jetset.backend import RGBMatrix, RGBMatrixOptions  # noqa: E402
from jetset.models import Airport, Flight, FlightRoute  # noqa: E402
from jetset.renderer import render_flight_card  # noqa: E402

AIRLINE = sys.argv[1] if len(sys.argv) > 1 else "UAL"
CYCLES = int(sys.argv[2]) if len(sys.argv) > 2 else 3
PAGE_HOLD = 4

flight = Flight(
    callsign=f"{AIRLINE}2337",
    aircraft="B738",
    route=FlightRoute(Airport("IAH"), Airport("LAX")),
    altitude=35000,
    speed=450,
    track=270.0,
    vertical_rate=1500,
)

options = RGBMatrixOptions()
options.cols = 64
options.rows = 32
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 5
options.multiplexing = 0
options.row_address_type = 0
options.panel_type = ""
options.pwm_bits = 6
options.led_rgb_sequence = "RBG"
options.disable_hardware_pulsing = True
options.drop_privileges = False  # the fix — stay root so the render loop can read logos

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

print(f">>> {flight.callsign}  IAH-LAX  B738 — real card, drop_privileges=False, x{CYCLES}.")
print(f"    Logo (airline {AIRLINE}) should now show top-right; text should stay clean.")
for _ in range(CYCLES):
    for page in range(4):
        render_flight_card(canvas, flight, metric_page=page)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(PAGE_HOLD)

matrix.Clear()
print(">>> done")
