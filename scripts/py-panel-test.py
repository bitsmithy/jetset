#!/usr/bin/env python3
"""On-Pi isolation test: drives the panel directly via the rgbmatrix Python
bindings to find where the app's render path diverges from the (working) C demo.

The C `demo` binary renders cleanly, so the hardware + flags are good. This
walks the Python draw path one stage at a time — solid fill, geometry border,
then BDF text — so we can see exactly which stage garbles.

Run on the Pi (root needed for GPIO):
    cd ~/jetset && sudo -E env PATH=$PATH uv run python scripts/py-panel-test.py
"""

import time

# --- Stage 0: backend probe -------------------------------------------------
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
except ImportError as exc:  # pragma: no cover - hardware-only path
    print(f"FAIL: cannot import rgbmatrix (incl. graphics): {exc}")
    raise SystemExit(1) from exc
print("OK: imported rgbmatrix incl. graphics")

WIDTH, HEIGHT = 64, 32

# Match the WORKING C-demo baseline as closely as possible: only the flags the
# demo used, nothing extra (no pwm_bits / multiplexing / panel_type / rgb_seq).
options = RGBMatrixOptions()
options.cols = WIDTH
options.rows = HEIGHT
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)


def hold(label: str, seconds: int = 4) -> None:
    print(f">>> {label}  ({seconds}s)")
    time.sleep(seconds)


# --- Stage A: solid fill across the whole panel -----------------------------
canvas = matrix.CreateFrameCanvas()
canvas.Fill(40, 0, 0)  # dim red
canvas = matrix.SwapOnVSync(canvas)
hold("A: whole panel dim RED — should fill ALL 64x32 evenly")

# --- Stage B: 1px border to verify dimensions/mapping -----------------------
canvas.Clear()
for x in range(WIDTH):
    canvas.SetPixel(x, 0, 0, 60, 0)
    canvas.SetPixel(x, HEIGHT - 1, 0, 60, 0)
for y in range(HEIGHT):
    canvas.SetPixel(0, y, 0, 60, 0)
    canvas.SetPixel(WIDTH - 1, y, 0, 60, 0)
canvas = matrix.SwapOnVSync(canvas)
hold("B: GREEN border hugging all four edges — clean rectangle?")

# --- Stage C: BDF text on four rows (the app's actual draw path) ------------
canvas.Clear()
font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")
white = graphics.Color(255, 255, 255)
graphics.DrawText(canvas, font, 1, 7, white, "ABCD")
graphics.DrawText(canvas, font, 1, 15, white, "1234")
graphics.DrawText(canvas, font, 1, 23, white, "wxyz")
graphics.DrawText(canvas, font, 1, 31, white, "EDGE")
canvas = matrix.SwapOnVSync(canvas)
hold("C: four rows of text top-to-bottom — all four readable?", 8)

matrix.Clear()
print("done")
