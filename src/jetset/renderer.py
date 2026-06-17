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

# Faulty-panel workaround: render everything in red (the deployed panel
# suppresses other channels when red is present). Set False once a standard
# panel is installed to restore the full palette and full-colour logos.
MONOCHROME_RED = True

FONT_HEIGHT = 7
font = graphics.Font()
font.LoadFont("fonts/5x7.bdf")

CANVAS_WIDTH = 64
LOGO_WIDTH = 20
LOGO_HEIGHT = 16


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


def render_logo(canvas: Canvas, flight: Flight) -> None:
    """Draw the airline logo, centred in the top-right corner.

    Honours MONOCHROME_RED (renders the logo as a red-luminance silhouette
    while the faulty panel can't do colour). Silently skips if no logo exists.
    """
    scaled = _scaled_logo(flight.airline)
    if scaled is None:
        return

    new_w, new_h = scaled.size
    x_offset = CANVAS_WIDTH - LOGO_WIDTH + (LOGO_WIDTH - new_w) // 2
    y_offset = (LOGO_HEIGHT - new_h) // 2

    for y in range(new_h):
        for x in range(new_w):
            r, g, b, a = scaled.getpixel((x, y))
            if a == 0 or (r, g, b) == (0, 0, 0):
                continue
            if MONOCHROME_RED:
                lum = round(0.299 * r + 0.587 * g + 0.114 * b)
                canvas.SetPixel(x_offset + x, y_offset + y, lum, 0, 0)
            else:
                canvas.SetPixel(x_offset + x, y_offset + y, r, g, b)


def render_flight_card(canvas: Canvas, flight: Flight, metric_page=0):
    canvas.Clear()

    # y-values are based off of the font height. Colours come from the palette,
    # but collapse to red while MONOCHROME_RED is set (faulty-panel workaround).
    rows = (
        (flight_label(flight), ORANGE),
        (route_label(flight), CYAN),
        (aircraft_label(flight), GREEN),
        (metrics_label(flight, metric_page), BLUE),
    )
    for i, (text, color) in enumerate(rows):
        draw_text(canvas, 1, FONT_HEIGHT * (i + 1) + i, text, RED if MONOCHROME_RED else color)

    render_logo(canvas, flight)


def render_loading(canvas: Canvas, page=0):
    canvas.Clear()

    draw_text(canvas, 1, FONT_HEIGHT * 1 + 0, loading_label(page), RED)
