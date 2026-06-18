"""Tests for the main loop."""

import time
from unittest.mock import patch

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


class TestAppSafeFetch:
    def test_swallows_fetch_errors_so_the_loop_survives(self) -> None:
        from unittest.mock import patch

        from jetset.app import App

        app = App(AppConfig())
        # An unexpected error in a fetch cycle must not propagate out of
        # _safe_fetch — the display keeps running on existing flights.
        with patch.object(app, "_fetch", side_effect=RuntimeError("boom")):
            app._safe_fetch()

        assert len(app.buffer) == 0


class TestAppFetchLoop:
    def test_runs_a_fetch_cycle_then_honors_stop(self) -> None:
        from unittest.mock import patch

        from jetset.app import App

        app = App(AppConfig())

        # One cycle: fetch is due so _safe_fetch runs, then the stop event is
        # set during the inter-cycle wait so the loop exits (no infinite spin).
        with (
            patch.object(app, "_should_fetch", return_value=True),
            patch.object(app, "_safe_fetch") as mock_fetch,
            patch.object(app._stop, "wait", side_effect=lambda *_a: app._stop.set()),
        ):
            app._fetch_loop()

        mock_fetch.assert_called_once()


class TestAppCurrentFrame:
    def test_cycles_window_flights_through_metric_pages(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        app.buffer.set_all([Flight(callsign="UAL2337"), Flight(callsign="SWA45")])
        app.last_fetch = 1000.0

        frames: list[tuple[str, int]] = []
        # elapsed == 0 → window_start == 0, so the window is [UAL2337, SWA45].
        with patch("jetset.app.time.time", return_value=1000.0):
            for frame_idx in range(8):
                app.frame = frame_idx
                result = app._current_frame()
                assert result is not None
                frames.append((result.flight.callsign, result.metric_page))

        assert frames == [
            ("UAL2337", 0), ("UAL2337", 1), ("UAL2337", 2), ("UAL2337", 3),
            ("SWA45", 0), ("SWA45", 1), ("SWA45", 2), ("SWA45", 3),
        ]

    def test_window_slides_over_the_refresh_interval(self) -> None:
        from jetset.app import App

        app = App(AppConfig())  # refresh = 2700s
        app.buffer.set_all([Flight(callsign=str(i)) for i in range(10)])
        app.last_fetch = 0.0
        app.frame = 0

        # slide_interval = 2700 / 10 = 270s; one slide advances window_start by 1.
        with patch("jetset.app.time.time", return_value=0.0):
            frame = app._current_frame()
            assert frame is not None
            assert frame.flight.callsign == "0"
        with patch("jetset.app.time.time", return_value=270.0):
            frame = app._current_frame()
            assert frame is not None
            assert frame.flight.callsign == "1"
        with patch("jetset.app.time.time", return_value=540.0):
            frame = app._current_frame()
            assert frame is not None
            assert frame.flight.callsign == "2"

    def test_empty_buffer_returns_none(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        assert app._current_frame() is None


class TestAppLoop:
    def _run_once(self, app):
        """Run App.loop for one iteration; sleep raises to break out cleanly.

        last_fetch is set so the background fetch thread stays off the network
        for the duration of the test.
        """
        app.last_fetch = time.time()
        with (
            patch("jetset.app.build_matrix"),
            patch("jetset.app.Renderer") as mock_renderer,
            patch("jetset.app.time.sleep", side_effect=KeyboardInterrupt),
        ):
            app.loop()
        return mock_renderer.return_value

    def test_renders_flight_card_and_advances_frame(self) -> None:
        from jetset.app import App

        app = App(AppConfig())
        app.buffer.set_all([Flight(callsign="UAL2337")])

        renderer = self._run_once(app)

        renderer.flight_card.assert_called_once_with(Flight(callsign="UAL2337"), 0)
        renderer.present.assert_called_once()
        assert app.frame == 1

    def test_renders_loading_when_buffer_empty(self) -> None:
        from jetset.app import App

        renderer = self._run_once(App(AppConfig()))

        renderer.loading.assert_called_once_with(0)
        renderer.present.assert_called_once()

    def test_loading_animation_cycles_with_frame(self) -> None:
        from jetset.app import App

        app = App(AppConfig())  # empty buffer
        app.frame = 5  # past the first cycle — must wrap, not freeze on "LOADING"

        renderer = self._run_once(app)

        # 5 % 4 == 1 → "LOADING." so the dots keep animating
        renderer.loading.assert_called_once_with(1)
