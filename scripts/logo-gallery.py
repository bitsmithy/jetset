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
from jetset.renderer import Renderer

HOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
PREFIX = sys.argv[2].upper() if len(sys.argv) > 2 else ""

logo_dir = Path(AppConfig.load(os.environ.get("JETSET_CONFIG")).logo_dir)
logos = sorted(p for p in logo_dir.glob("*.png") if p.stem.upper().startswith(PREFIX))
if not logos:
    raise SystemExit(f"No logos matching '{PREFIX}*' in {logo_dir}")

renderer = Renderer(build_matrix(), logo_dir)
print(f"{len(logos)} logos in {logo_dir} — {HOLD}s each (Ctrl-C to stop)")

try:
    for path in logos:
        # A bare Flight shows just the code (callsign row) + the logo; the other
        # rows render empty since route/aircraft/metrics are absent.
        renderer.flight_card(Flight(callsign=path.stem))
        renderer.present()
        print(f">>> {path.stem}")
        time.sleep(HOLD)
except KeyboardInterrupt:
    pass
finally:
    renderer.clear()
    print("done")
