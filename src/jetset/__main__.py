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
    _configure_logging()

    config = AppConfig.load(os.environ.get("JETSET_CONFIG"))

    from jetset.backend import IS_HARDWARE, RGBMatrix, RGBMatrixOptions

    options = RGBMatrixOptions()
    options.cols = DISPLAY_WIDTH
    options.rows = DISPLAY_HEIGHT
    if IS_HARDWARE:
        # Physical-panel tuning. These are hardware-only knobs; the emulator
        # neither needs nor accepts them, so they stay behind IS_HARDWARE.
        options.hardware_mapping = "adafruit-hat"
        options.gpio_slowdown = config.hardware_gpio_slowdown
        options.multiplexing = 0
        options.row_address_type = 1
        options.panel_type = config.hardware_panel_type
        options.pwm_bits = 6  # lower PWM reduces flicker on Pi 3 A+
        options.led_rgb_sequence = config.hardware_rgb_sequence
        options.disable_hardware_pulsing = True

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()
    try:
        logger.info("Press Ctrl-C to stop")
        import time

        time.sleep(1)
        app = App(config)
        app.loop(matrix, canvas)
    except KeyboardInterrupt:
        logger.info("Shutdown.")


if __name__ == "__main__":
    main()
