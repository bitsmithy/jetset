"""Tests for the flight card renderer."""

from pathlib import Path


class TestBdfFont:
    def test_font_file_exists(self) -> None:
        font_path = Path("fonts/5x7.bdf")
        assert font_path.exists(), "5x7.bdf font not found"

    def test_font_loads_via_graphics(self) -> None:
        from RGBMatrixEmulator import graphics

        font = graphics.Font()
        font.LoadFont(str(Path("fonts/5x7.bdf").resolve()))
        assert font.height == 7
        assert font.CharacterWidth(ord("A")) == 5


class TestRenderFlightCard:
    def test_clears_canvas_before_drawing(self) -> None:
        from unittest.mock import MagicMock
        from jetset.models import Flight
        from jetset.renderer import render_flight_card

        canvas = MagicMock()
        canvas.width = 64
        flight = Flight(callsign="UAL2337")

        render_flight_card(canvas, flight)

        assert canvas.Clear.called

    def test_renders_all_metric_pages_without_error(self) -> None:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
        from jetset.models import Flight
        from jetset.renderer import render_flight_card

        options = RGBMatrixOptions()
        options.cols = 64
        options.rows = 32
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        flight = Flight(
            callsign="UAL2337",
            altitude=35000, speed=450,
            vertical_rate=1500, track=270,
        )

        for page in range(4):
            render_flight_card(canvas, flight, metric_page=page)
            canvas = matrix.SwapOnVSync(canvas)
