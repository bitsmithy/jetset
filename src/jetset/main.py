import time

from RGBMatrixEmulator.emulation.canvas import Canvas
from RGBMatrixEmulator.emulation.matrix import RGBMatrix

from jetset.models import Flight
from jetset.renderer import render_flight_card


def run_demo(matrix: RGBMatrix, canvas: Canvas, flight: Flight):
    page = 0

    for _ in range(4):
        render_flight_card(canvas, flight, page)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(2)
        page = (page + 1) % 4
