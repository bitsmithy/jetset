"""Selects the LED matrix backend once, for the whole app to share.

Prefers the real rpi-rgb-led-matrix library (on the Pi) and falls back to the
emulator (on a dev machine). The emulator mirrors the rpi-rgb-led-matrix API,
so the rest of the app is backend-agnostic — but every component MUST use the
SAME backend. Drawing with the emulator's `graphics` onto a hardware canvas
produces garbled output, because the two libraries' canvas internals differ.
Importing `graphics`, `RGBMatrix`, and `RGBMatrixOptions` from here guarantees
the matrix and the drawing engine never drift apart.
"""

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

    IS_HARDWARE = True
except ImportError:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics

    IS_HARDWARE = False

__all__ = ["RGBMatrix", "RGBMatrixOptions", "graphics", "IS_HARDWARE"]
