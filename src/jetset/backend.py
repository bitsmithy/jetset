"""Selects the LED matrix backend once, for the whole app to share.

Prefers the real rpi-rgb-led-matrix library (on the Pi) and falls back to the
emulator (on a dev machine). The emulator mirrors the rpi-rgb-led-matrix API,
so the rest of the app is backend-agnostic — but every component MUST use the
SAME backend. Drawing with the emulator's `graphics` onto a hardware canvas
produces garbled output, because the two libraries' canvas internals differ.
Importing `graphics`, `RGBMatrix`, and `RGBMatrixOptions` from here guarantees
the matrix and the drawing engine never drift apart.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

    IS_HARDWARE = True
except ImportError as exc:
    # rgbmatrix simply being absent is the normal dev-machine case — fall back
    # quietly. But if rgbmatrix is *present* and failed for another reason (a
    # missing dependency, a broken/removed build), warn loudly so the Pi never
    # silently runs the emulator.
    rgbmatrix_absent = isinstance(exc, ModuleNotFoundError) and exc.name == "rgbmatrix"
    if not rgbmatrix_absent:
        logger.warning("rgbmatrix present but failed to import (%r) — using emulator", exc)

    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics

    IS_HARDWARE = False

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32


def build_matrix() -> RGBMatrix:
    """Create the 64x32 LED matrix with the project's standard options.

    The single place panel setup lives, so the app and the scripts/ probes never
    drift. On hardware it sets the Adafruit HAT mapping and keeps the process as
    root (drop_privileges off) so the render loop can still read the logo cache
    under /home — the library otherwise drops to 'daemon', which can't traverse
    /home/pi. The emulator rejects hardware-only knobs, so they stay behind
    IS_HARDWARE.
    """
    options = RGBMatrixOptions()
    options.cols = DISPLAY_WIDTH
    options.rows = DISPLAY_HEIGHT
    if IS_HARDWARE:
        options.hardware_mapping = "adafruit-hat"
        options.drop_privileges = False
    return RGBMatrix(options=options)


__all__ = [
    "RGBMatrix",
    "RGBMatrixOptions",
    "graphics",
    "IS_HARDWARE",
    "build_matrix",
    "DISPLAY_WIDTH",
    "DISPLAY_HEIGHT",
]
