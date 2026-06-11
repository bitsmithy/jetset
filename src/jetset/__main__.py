"""Minimal emulator smoke test — proves the LED matrix emulator works."""

from jetset.main import run_demo
from jetset.models import Flight

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
    flight = Flight(
        callsign="UAL2337",
        origin="SFO",
        destination="LAX",
        aircraft="A320",
        altitude=35000,
        speed=450,
        track=270,
        vertical_rate=1500,
    )

    try:
        print("Press Ctrl-C to stop")
        while True:
            run_demo(matrix, canvas, flight)
    except KeyboardInterrupt:
        canvas.Clear()
        matrix.SwapOnVSync(canvas)
        print("\nShutdown.")


if __name__ == "__main__":
    main()
