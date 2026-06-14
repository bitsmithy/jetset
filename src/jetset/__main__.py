"""Minimal emulator smoke test — proves the LED matrix emulator works."""

from jetset.app import App
from jetset.config import AppConfig

DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32


def main() -> None:
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    except ImportError:
        print("RGBMatrixEmulator not installed. Run: uv add RGBMatrixEmulator")
        return

    options = RGBMatrixOptions()
    options.cols = DISPLAY_WIDTH
    options.rows = DISPLAY_HEIGHT

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    try:
        print("Press Ctrl-C to stop")
        config = AppConfig()
        app = App(config)
        app.loop(matrix, canvas)
    except KeyboardInterrupt:
        print("\nShutdown.")


if __name__ == "__main__":
    main()
