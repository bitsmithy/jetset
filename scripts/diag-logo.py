#!/usr/bin/env python3
"""Diagnose why the root service can't load a logo that the pi user can.
Run as root the same way the service does:
  sudo -E env PATH="$PATH" uv run python scripts/diag-logo.py
"""

import os
from pathlib import Path

print("euid:", os.geteuid(), "HOME:", os.environ.get("HOME"))
print("SUDO_USER:", os.environ.get("SUDO_USER"))
print("JETSET_LOGO_DIR (pre-set):", os.environ.get("JETSET_LOGO_DIR"))

if "JETSET_LOGO_DIR" not in os.environ:
    su = os.environ.get("SUDO_USER")
    base = Path(f"/home/{su}") if su else Path.home()
    os.environ["JETSET_LOGO_DIR"] = str(base / ".cache" / "jetset" / "logos")
print("JETSET_LOGO_DIR (effective):", os.environ["JETSET_LOGO_DIR"])

p = Path(os.environ["JETSET_LOGO_DIR"]) / "UAL.png"
print("path:", p)
print("  exists:", p.exists(), " os.access R_OK:", os.access(p, os.R_OK))
for d in [Path("/home"), Path("/home/pi"), Path("/home/pi/.cache"), p.parent]:
    print("  traverse", d, "X_OK:", os.access(d, os.X_OK), "R_OK:", os.access(d, os.R_OK))

from jetset.display import LOGO_DIR, load_logo  # noqa: E402

print("LOGO_DIR (display):", LOGO_DIR)
print("LOGO_DIR == env?", str(LOGO_DIR) == os.environ["JETSET_LOGO_DIR"])

try:
    from PIL import Image

    img = Image.open(p)
    img.load()
    print("PIL open: OK", img.size)
except Exception as e:  # noqa: BLE001 - diagnostic
    print("PIL open FAILED:", type(e).__name__, repr(e))

print("load_logo('UAL'):", load_logo("UAL"))
