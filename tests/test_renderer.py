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

    def test_all_rows_are_red(self) -> None:
        # The deployed panel suppresses other channels when red is present, so
        # every row is red (single working channel) until a standard panel.
        from unittest.mock import MagicMock, patch

        from jetset import renderer
        from jetset.models import Flight

        canvas = MagicMock()
        flight = Flight(callsign="UAL2337", altitude=35000)

        with patch("jetset.renderer.draw_text") as mock_draw:
            renderer.render_flight_card(canvas, flight)

        row_colors = [call.args[4] for call in mock_draw.call_args_list]
        assert row_colors == [renderer.RED] * 4

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


class TestRenderLogo:
    def test_skips_missing_airline(self) -> None:
        from unittest.mock import patch

        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

        from jetset.models import Flight
        from jetset.renderer import _scaled_logo, render_logo

        options = RGBMatrixOptions()
        options.cols = 64
        options.rows = 32
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        flight = Flight(callsign="UAL2337")
        with patch("jetset.renderer.load_logo", return_value=None):
            _scaled_logo.cache_clear()  # so the patched load_logo is used
            render_logo(canvas, flight)  # no crash

    def test_draws_pixels_for_known_airline(self) -> None:
        from unittest.mock import patch

        from PIL import Image
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

        from jetset.models import Flight
        from jetset.renderer import LOGO_WIDTH, _scaled_logo, render_logo

        test_logo = Image.new("RGB", (LOGO_WIDTH, 20), (255, 0, 0))

        options = RGBMatrixOptions()
        options.cols = 64
        options.rows = 32
        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        flight = Flight(callsign="UAL2337", aircraft="B738")
        with patch("jetset.renderer.load_logo", return_value=test_logo):
            _scaled_logo.cache_clear()  # so the patched load_logo is used
            with patch.object(canvas, "SetPixel") as mock_setpixel:
                render_logo(canvas, flight)

        mock_setpixel.assert_called()
