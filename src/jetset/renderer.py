from RGBMatrixEmulator import graphics
from RGBMatrixEmulator.emulation.canvas import Canvas

from jetset.display import aircraft_label, flight_label, metrics_label, route_label
from jetset.models import Flight

# Colour palette
ORANGE = (255, 140, 0)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
WHITE = (255, 255, 255)
DIM_WHITE = (80, 80, 80)
BLACK = (0, 0, 0)

FONT_HEIGHT = 7
font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")


def draw_text(canvas: Canvas, x: int, y: int, text: str, color: tuple[int, int, int]) -> None:
    c = graphics.Color(*color)
    graphics.DrawText(canvas, font, x, y, c, text)


def render_flight_card(canvas: Canvas, flight: Flight, metric_page=0):
    canvas.Clear()

    # y-values are based off of the font height
    draw_text(canvas, 1, FONT_HEIGHT * 1 + 0, flight_label(flight), ORANGE)
    draw_text(canvas, 1, FONT_HEIGHT * 2 + 1, route_label(flight), CYAN)
    draw_text(canvas, 1, FONT_HEIGHT * 3 + 2, aircraft_label(flight), GREEN)
    draw_text(canvas, 1, FONT_HEIGHT * 4 + 3, metrics_label(flight, metric_page), BLUE)
