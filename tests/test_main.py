"""Tests for the main demo loop."""

from unittest.mock import MagicMock, patch

from jetset.models import Flight


def test_run_demo_cycles_through_four_pages() -> None:
    """run_demo() should call render_flight_card with pages 0,1,2,3 once."""
    from jetset.main import run_demo

    mock_canvas = MagicMock()
    mock_canvas.width = 64
    mock_matrix = MagicMock()

    flight = Flight(
        callsign="UAL2337",
        origin="SFO",
        destination="LAX",
        altitude=35000,
        speed=450,
        track=270,
        vertical_rate=1500,
    )

    pages_called: list[int] = []
    with patch("jetset.main.render_flight_card") as mock_render:
        def track_page(canvas, flight, metric_page: int = 0) -> None:  # type: ignore[no-untyped-def]
            pages_called.append(metric_page)

        mock_render.side_effect = track_page

        run_demo(mock_matrix, mock_canvas, flight)

    assert pages_called == [0, 1, 2, 3]
    assert mock_matrix.SwapOnVSync.call_count == 4
