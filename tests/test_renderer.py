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
        # ord() gives the codepoint int the real rpi-rgb-led-matrix API wants;
        # the emulator stub mistypes the param as str.
        assert font.CharacterWidth(ord("A")) == 5  # ty: ignore[invalid-argument-type]


def _renderer(logo_dir: str = "logos"):
    """A Renderer backed by an emulator matrix, for tests."""
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions

    from jetset.renderer import Renderer

    options = RGBMatrixOptions()
    options.cols = 64
    options.rows = 32
    return Renderer(RGBMatrix(options=options), Path(logo_dir))


class TestFlightCard:
    def test_clears_canvas_before_drawing(self) -> None:
        from unittest.mock import patch

        from jetset.models import Flight

        renderer = _renderer()
        with patch.object(renderer._canvas, "Clear") as mock_clear:
            renderer.flight_card(Flight(callsign="UAL2337"))

        mock_clear.assert_called()

    def test_each_row_uses_its_palette_colour(self) -> None:
        # Each row is drawn in its own palette colour.
        from unittest.mock import patch

        from jetset import renderer as r
        from jetset.models import Flight

        rnd = _renderer()
        with patch("jetset.renderer.draw_text") as mock_draw:
            rnd.flight_card(Flight(callsign="UAL2337", altitude=35000))

        row_colors = [call.args[4] for call in mock_draw.call_args_list]
        assert row_colors == [r.ORANGE, r.CYAN, r.GREEN, r.BLUE]

    def test_renders_all_metric_pages_without_error(self) -> None:
        from jetset.models import Flight

        renderer = _renderer()
        flight = Flight(
            callsign="UAL2337",
            altitude=35000, speed=450,
            vertical_rate=1500, track=270,
        )
        for page in range(4):
            renderer.flight_card(flight, page)
            renderer.present()


class TestLogo:
    def test_skips_missing_airline(self) -> None:
        from unittest.mock import patch

        from jetset.models import Flight
        from jetset.renderer import _scaled_logo

        renderer = _renderer()
        flight = Flight(callsign="UAL2337")
        with patch("jetset.renderer.load_logo", return_value=None):
            _scaled_logo.cache_clear()  # so the patched load_logo is used
            renderer._logo(flight)  # no crash
        _scaled_logo.cache_clear()

    def test_draws_pixels_for_known_airline(self) -> None:
        from unittest.mock import patch

        from PIL import Image

        from jetset.models import Flight
        from jetset.renderer import LOGO_WIDTH, _scaled_logo

        test_logo = Image.new("RGB", (LOGO_WIDTH, 20), (255, 0, 0))
        renderer = _renderer()
        flight = Flight(callsign="UAL2337", aircraft="B738")
        with patch("jetset.renderer.load_logo", return_value=test_logo):
            _scaled_logo.cache_clear()  # so the patched load_logo is used
            with patch.object(renderer._canvas, "SetPixel") as mock_setpixel:
                renderer._logo(flight)
        _scaled_logo.cache_clear()

        mock_setpixel.assert_called()
