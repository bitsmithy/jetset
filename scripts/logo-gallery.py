#!/usr/bin/env python3
"""Cycle through every cached airline logo on the panel so you can eyeball the
whole set without waiting for a live flight to match. Each logo is shown the way
a real card would: the ICAO code where the callsign goes (top-left), the logo
where it goes (top-right).

Run on the Pi with the service stopped:
  sudo systemctl stop jetset
  sudo -E env PATH="$PATH" uv run python scripts/logo-gallery.py [seconds] [prefix]
  sudo systemctl start jetset

  seconds : hold per logo (default 3)
  prefix  : only show codes starting with this (e.g. "U" or "DAL"); default all
"""

import os
import sys
import time
from pathlib import Path

from jetset.backend import build_matrix
from jetset.config import AppConfig
from jetset.models import Flight
from jetset.renderer import ORANGE, draw_text, render_logo

HOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
PREFIX = sys.argv[2].upper() if len(sys.argv) > 2 else ""

logo_dir = Path(AppConfig.load(os.environ.get("JETSET_CONFIG")).logo_dir)
logos = sorted(p for p in logo_dir.glob("*.png") if p.stem.upper().startswith(PREFIX))
if not logos:
    raise SystemExit(f"No logos matching '{PREFIX}*' in {logo_dir}")

matrix = build_matrix()
canvas = matrix.CreateFrameCanvas()

print(f"{len(logos)} logos in {logo_dir} — {HOLD}s each (Ctrl-C to stop)")

try:
    for path in logos:
        code = path.stem
        flight = Flight(callsign=code)
        canvas.Clear()
        draw_text(canvas, 1, 7, code, ORANGE)  # ICAO where the callsign goes
        render_logo(canvas, flight, logo_dir)  # logo where it goes
        canvas = matrix.SwapOnVSync(canvas)
        print(f">>> {code}")
        time.sleep(HOLD)
except KeyboardInterrupt:
    pass
finally:
    matrix.Clear()
    print("done")
