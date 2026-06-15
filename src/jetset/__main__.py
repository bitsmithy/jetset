"""Minimal emulator smoke test — proves the LED matrix emulator works."""

import logging
import os

from jetset.app import App
from jetset.config import AppConfig

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if os.environ.get("JETSET_DEBUG"):
        logging.getLogger("jetset").setLevel(logging.DEBUG)

    # RGBMatrixEmulator has its own handler — stop propagation to avoid
    # duplicate INFO lines in the root logger.
    logging.getLogger("RGBME").propagate = False
def main() -> None:
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    except ImportError:
        print("RGBMatrixEmulator not installed. Run: uv add RGBMatrixEmulator")
        return

    _configure_logging()

    options = RGBMatrixOptions()
    options.cols = DISPLAY_WIDTH
    options.rows = DISPLAY_HEIGHT

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()
    try:
        logger.info("Press Ctrl-C to stop")
        import time

        time.sleep(1)
        config = AppConfig()
        app = App(config)
        app.loop(matrix, canvas)
    except KeyboardInterrupt:
        logger.info("Shutdown.")


if __name__ == "__main__":
    main()
