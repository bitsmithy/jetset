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

# Point the loader at the invoking user's cache before importing app modules.
# Under sudo, Path.home() is /root, so prefer SUDO_USER's home.
if "JETSET_LOGO_DIR" not in os.environ:
    sudo_user = os.environ.get("SUDO_USER")
    base = Path(f"/home/{sudo_user}") if sudo_user else Path.home()
    os.environ["JETSET_LOGO_DIR"] = str(base / ".cache" / "jetset" / "logos")

from jetset.backend import build_matrix  # noqa: E402
from jetset.display import LOGO_DIR  # noqa: E402
from jetset.renderer import ORANGE, draw_text, render_logo  # noqa: E402

HOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
PREFIX = sys.argv[2].upper() if len(sys.argv) > 2 else ""

matrix = build_matrix()
canvas = matrix.CreateFrameCanvas()

logos = sorted(p for p in LOGO_DIR.glob("*.png") if p.stem.upper().startswith(PREFIX))
if not logos:
    raise SystemExit(f"No logos matching '{PREFIX}*' in {LOGO_DIR}")

print(f"{len(logos)} logos in {LOGO_DIR} — {HOLD}s each (Ctrl-C to stop)")

try:
    for path in logos:
        code = path.stem
        flight = type("GalleryFlight", (), {"airline": code})()
        canvas.Clear()
        draw_text(canvas, 1, 7, code, ORANGE)  # ICAO where the callsign goes
        render_logo(canvas, flight)  # logo where it goes
        canvas = matrix.SwapOnVSync(canvas)
        print(f">>> {code}")
        time.sleep(HOLD)
except KeyboardInterrupt:
    pass
finally:
    matrix.Clear()
    print("done")
