"""Minimal emulator smoke test — proves the LED matrix emulator works."""

import time


def main() -> None:
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    except ImportError:
        print("RGBMatrixEmulator not installed. Run: uv add RGBMatrixEmulator")
        return

    options = RGBMatrixOptions()
    options.cols = 64
    options.rows = 32

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    # Draw some test pixels — red at top-left, green at top-right,
    # blue at bottom-left, white at bottom-right
    canvas.SetPixel(0, 0, 255, 0, 0)
    canvas.SetPixel(63, 0, 0, 255, 0)
    canvas.SetPixel(0, 31, 0, 0, 255)
    canvas.SetPixel(63, 31, 255, 255, 255)

    # Draw a diagonal line
    for i in range(32):
        canvas.SetPixel(i * 2, i, 255, 140, 0)

    canvas = matrix.SwapOnVSync(canvas)

    print("Emulator window open at http://localhost:8888/")
    print("Running for 10 seconds then exiting...")
    time.sleep(10)


if __name__ == "__main__":
    main()
