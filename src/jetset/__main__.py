"""Entry point: fetch nearby flights from AirLabs and render the flight board
on the LED matrix (real rpi-rgb-led-matrix on the Pi, emulator elsewhere)."""

import logging
import os

from jetset.app import App
from jetset.config import AppConfig

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
    _configure_logging()

    # Load AIRLABS_API_KEY (and friends) from a .env file if present.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    config = AppConfig.load(os.environ.get("JETSET_CONFIG"))

    try:
        logger.info("Press Ctrl-C to stop")
        import time

        time.sleep(1)
        app = App(config)
        app.loop()
    except KeyboardInterrupt:
        logger.info("Shutdown.")


if __name__ == "__main__":
    main()
