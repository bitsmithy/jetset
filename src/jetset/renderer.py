from functools import lru_cache

from PIL import Image
from RGBMatrixEmulator.emulation.canvas import Canvas

from jetset.backend import graphics
from jetset.display import (
    aircraft_label,
    flight_label,
    load_logo,
    loading_label,
    metrics_label,
    route_label,
)
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

CANVAS_WIDTH = 64
# Logo box, top-right corner, over the top three text rows (row 4/metrics can
# run full-width, so the box stops above it). A square logo scales to
# LOGO_WIDTH x LOGO_HEIGHT; the margins keep it one pixel off the top and right
# edges. With these values the logo spans cols 40-62, rows 1-23.
LOGO_WIDTH = 23
LOGO_HEIGHT = 23
LOGO_RIGHT_MARGIN = 1  # empty columns kept to the right of the logo
LOGO_TOP_MARGIN = 1  # empty rows kept above the logo
# Debug aid: outline the logo box on the panel so its bounds can be eyeballed
# against the card. Set False for normal use.
LOGO_DEBUG_BORDER = False


def draw_text(canvas: Canvas, x: int, y: int, text: str, color: tuple[int, int, int]) -> None:
    c = graphics.Color(*color)
    graphics.DrawText(canvas, font, x, y, c, text)


@lru_cache(maxsize=256)
def _scaled_logo(airline_code: str) -> Image.Image | None:
    """Load + proportionally scale an airline logo to fit the logo box, cached.

    Decoding and resizing happen once per airline, not every frame.
    """
    img = load_logo(airline_code)
    if img is None:
        return None
    img = img.convert("RGBA")
    src_w, src_h = img.size
    scale = min(LOGO_WIDTH / src_w, LOGO_HEIGHT / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)


def _draw_logo_border(canvas: Canvas) -> None:
    """Outline the logo box (debug aid for checking its bounds on the panel)."""
    left = CANVAS_WIDTH - LOGO_RIGHT_MARGIN - LOGO_WIDTH
    right = left + LOGO_WIDTH - 1
    top = LOGO_TOP_MARGIN
    bottom = top + LOGO_HEIGHT - 1
    for x in range(left, right + 1):
        canvas.SetPixel(x, top, 255, 0, 0)
        canvas.SetPixel(x, bottom, 255, 0, 0)
    for y in range(top, bottom + 1):
        canvas.SetPixel(left, y, 255, 0, 0)
        canvas.SetPixel(right, y, 255, 0, 0)


def render_logo(canvas: Canvas, flight: Flight) -> None:
    """Draw the airline logo in full colour, top-right. Skips if none exists."""
    if LOGO_DEBUG_BORDER:
        _draw_logo_border(canvas)

    scaled: Image.Image = _scaled_logo(flight.airline)
    if scaled is None:
        return

    new_w, new_h = scaled.size
    x_offset = CANVAS_WIDTH - LOGO_RIGHT_MARGIN - LOGO_WIDTH + (LOGO_WIDTH - new_w) // 2
    y_offset = LOGO_TOP_MARGIN + (LOGO_HEIGHT - new_h) // 2

    for y in range(new_h):
        for x in range(new_w):
            r, g, b, a = scaled.getpixel((x, y))
            if a == 0 or (r, g, b) == (0, 0, 0):
                continue
            canvas.SetPixel(x_offset + x, y_offset + y, r, g, b)


def render_flight_card(canvas: Canvas, flight: Flight, metric_page=0):
    canvas.Clear()

    # y-values are based off of the font height; each row uses its palette colour.
    rows = (
        (flight_label(flight), ORANGE),
        (route_label(flight), CYAN),
        (aircraft_label(flight), GREEN),
        (metrics_label(flight, metric_page), BLUE),
    )
    for i, (text, color) in enumerate(rows):
        draw_text(canvas, 1, FONT_HEIGHT * (i + 1) + i, text, color)

    render_logo(canvas, flight)


def render_loading(canvas: Canvas, page=0):
    canvas.Clear()

    draw_text(canvas, 1, FONT_HEIGHT * 1 + 0, loading_label(page), RED)
