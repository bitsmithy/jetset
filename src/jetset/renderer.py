from functools import lru_cache
from pathlib import Path
from typing import cast

from PIL import Image
from RGBMatrixEmulator.emulation.canvas import Canvas
from RGBMatrixEmulator.emulation.matrix import RGBMatrix

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


def draw_text(canvas: Canvas, x: int, y: int, text: str, color: tuple[int, int, int]) -> None:
    c = graphics.Color(*color)
    graphics.DrawText(canvas, font, x, y, c, text)


@lru_cache(maxsize=256)
def _scaled_logo(airline_code: str, logo_dir: Path) -> Image.Image | None:
    """Load + proportionally scale an airline logo to fit the logo box, cached.

    Decoding and resizing happen once per (airline, dir), not every frame.
    """
    img = load_logo(airline_code, logo_dir)
    if img is None:
        return None
    img = img.convert("RGBA")
    src_w, src_h = img.size
    scale = min(LOGO_WIDTH / src_w, LOGO_HEIGHT / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


class Renderer:
    """Owns the LED matrix's double-buffered canvas and the logo directory.

    Holding the canvas and logo_dir as state keeps them out of every draw call.
    present() performs the VSync buffer swap; the rest of the app just asks for
    a frame and presents it.
    """

    def __init__(self, matrix: RGBMatrix, logo_dir: Path) -> None:
        self._matrix = matrix
        self._logo_dir = logo_dir
        self._canvas = matrix.CreateFrameCanvas()

    def flight_card(self, flight: Flight, metric_page: int = 0) -> None:
        canvas = self._canvas
        canvas.Clear()
        # y-values are based off the font height; each row uses its palette colour.
        rows = (
            (flight_label(flight), ORANGE),
            (route_label(flight), CYAN),
            (aircraft_label(flight), GREEN),
            (metrics_label(flight, metric_page), BLUE),
        )
        for i, (text, color) in enumerate(rows):
            draw_text(canvas, 1, FONT_HEIGHT * (i + 1) + i, text, color)
        self._logo(flight)

    def loading(self, page: int = 0) -> None:
        self._canvas.Clear()
        draw_text(self._canvas, 1, FONT_HEIGHT * 1 + 0, loading_label(page), RED)

    def present(self) -> None:
        """Swap the drawn frame onto the panel and ready the back buffer."""
        self._canvas = self._matrix.SwapOnVSync(self._canvas)

    def clear(self) -> None:
        """Blank the panel."""
        self._canvas.Clear()
        self.present()

    def _logo(self, flight: Flight) -> None:
        """Draw the airline logo in full colour, top-right. Skips if none exists."""
        scaled: Image.Image | None = _scaled_logo(flight.airline, self._logo_dir)
        if scaled is None:
            return

        new_w, new_h = scaled.size
        x_offset = CANVAS_WIDTH - LOGO_RIGHT_MARGIN - LOGO_WIDTH + (LOGO_WIDTH - new_w) // 2
        y_offset = LOGO_TOP_MARGIN + (LOGO_HEIGHT - new_h) // 2

        for y in range(new_h):
            for x in range(new_w):
                r, g, b, a = cast(tuple[int, int, int, int], scaled.getpixel((x, y)))
                if a == 0 or (r, g, b) == (0, 0, 0):
                    continue
                self._canvas.SetPixel(x_offset + x, y_offset + y, r, g, b)
