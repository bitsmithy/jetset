"""Tests for the main loop."""

from unittest.mock import MagicMock, patch

from jetset.config import AppConfig
from jetset.models import Flight


class TestAppShouldFetch:
    def test_first_run_returns_true(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        with patch("jetset.app.time.time", return_value=0):
            assert app._should_fetch() is True

    def test_returns_true_when_past_interval(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        interval = app.config.refresh
        now = 10000
        with patch("jetset.app.time.time", return_value=now):
            app.last_fetch = now - interval - 1
            assert app._should_fetch() is True

            app.last_fetch = now - interval // 2
            assert app._should_fetch() is False

            app.last_fetch = now - interval
            assert app._should_fetch() is True


class TestAppFetch:
    def test_fetches_and_pushes_to_buffer(self) -> None:
        from jetset.app import App

        config = AppConfig()
        app = App(config)
        flights = [Flight(callsign="UAL2337"), Flight(callsign="SWA45")]

        with (
            patch.object(app.adapter, "nearby_flights", return_value=flights),
            patch("jetset.app.time.time", return_value=500),
        ):
            app._fetch()

        assert len(app.buffer) == 2
        assert app.last_fetch == 500


class TestAppCurrentFrame:
    def test_selects_flight_and_metric_page(self) -> None:
        from jetset.app import App

        config = AppConfig()
        app = App(config)
        app.buffer.push(Flight(callsign="UAL2337"))
        app.buffer.push(Flight(callsign="SWA45"))

        frames: list[tuple[str, int]] = []
        for frame_idx in range(8):
            app.frame = frame_idx
            result = app._current_frame()
            assert result is not None
            frames.append((result.flight.callsign, result.metric_page))

        assert frames == [
            ("UAL2337", 0),
            ("UAL2337", 1),
            ("UAL2337", 2),
            ("UAL2337", 3),
            ("SWA45", 0),
            ("SWA45", 1),
            ("SWA45", 2),
            ("SWA45", 3),
        ]

    def test_empty_buffer_returns_none(self) -> None:
        from jetset.app import App

        config = AppConfig()
        app = App(config)

        result = app._current_frame()
        assert result is None


class TestAppHistory:
    def test_refreshes_stale_flights_after_fetch(self) -> None:
        from unittest.mock import patch

        from jetset.app import App

        config = AppConfig()
        app = App(config)
        # Seed buffer with a flight not in the new live set
        stale = Flight(callsign="UAL2337")
        app.buffer.push(stale)
        # Live set returns only one different flight
        live = [Flight(callsign="SWA45")]

        with (
            patch.object(app.adapter, "nearby_flights", return_value=live),
            patch.object(app.adapter, "refresh_flight", return_value=stale) as mock_refresh,
            patch("jetset.app.time.time", return_value=500),
        ):
            app._fetch()

        # SWA45 was pushed to the buffer
        assert len(app.buffer) == 2
        # UAL2337 was refreshed via refresh_flight
        mock_refresh.assert_called_once_with(stale)


class TestAppRenderFrame:
    def test_renders_and_advances_frame(self) -> None:
        from jetset.app import App

        config = AppConfig()
        app = App(config)
        app.frame = 3

        mock_matrix = MagicMock()
        mock_canvas = MagicMock()
        frame = app.Frame(Flight(callsign="UAL2337"), 1)

        with (
            patch("jetset.app.render_flight_card") as mock_render,
            patch("jetset.app.time.sleep"),
        ):
            app._render_frame(mock_matrix, mock_canvas, frame)

        mock_render.assert_called_once_with(mock_canvas, frame.flight, frame.metric_page)
        mock_matrix.SwapOnVSync.assert_called_once_with(mock_canvas)
        assert app.frame == 4

    def test_returns_swapped_canvas_for_next_frame(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        mock_matrix = MagicMock()
        mock_canvas = MagicMock()
        frame = app.Frame(Flight(callsign="UAL2337"), 1)

        with (
            patch("jetset.app.render_flight_card"),
            patch("jetset.app.time.sleep"),
        ):
            next_canvas = app._render_frame(mock_matrix, mock_canvas, frame)

        # SwapOnVSync hands back the now-offscreen buffer; the next frame must
        # be drawn into it, not into the canvas we just displayed.
        assert next_canvas is mock_matrix.SwapOnVSync.return_value


class TestAppLoading:
    def test_renders_loading_when_buffer_empty(self) -> None:
        from jetset.app import App

        config = AppConfig()
        app = App(config)
        app.frame = 0

        mock_matrix = MagicMock()
        mock_canvas = MagicMock()

        with (
            patch("jetset.app.render_loading") as mock_render,
            patch("jetset.app.time.sleep"),
        ):
            next_canvas = app._render_loading(mock_matrix, mock_canvas)

        mock_render.assert_called_once_with(mock_canvas, 0)
        mock_matrix.SwapOnVSync.assert_called_once_with(mock_canvas)
        assert app.frame == 1
        assert next_canvas is mock_matrix.SwapOnVSync.return_value
