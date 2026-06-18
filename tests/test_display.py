"""Tests for display formatting functions."""

from jetset.models import Airport, Flight, FlightRoute


class TestLoadingLabel:
    def test_returns_loading_text(self) -> None:
        from jetset.display import loading_label

        assert loading_label() == "LOADING"


class TestLogo:
    def test_returns_none_for_missing_airline(self) -> None:
        from pathlib import Path

        from jetset.display import load_logo

        assert load_logo("NONEXIST", Path("/nonexistent")) is None


class TestFlightLabel:
    def test_returns_callsign(self) -> None:
        from jetset.display import flight_label

        flight = Flight(callsign="UAL2337")
        assert flight_label(flight) == "UAL2337"


class TestAircraftLabel:
    def test_returns_aircraft_when_set(self) -> None:
        from jetset.display import aircraft_label

        flight = Flight(callsign="UAL2337", aircraft="B738")
        assert aircraft_label(flight) == "B738"

    def test_returns_empty_when_missing(self) -> None:
        from jetset.display import aircraft_label

        flight = Flight(callsign="UAL2337")
        assert aircraft_label(flight) == ""


class TestRouteLabel:
    def test_route_label_when_both_set(self) -> None:
        from jetset.display import route_label

        flight = Flight(
            callsign="UAL2337",
            route=FlightRoute(Airport("SFO"), Airport("LAX")),
        )
        assert route_label(flight) == "SFO→LAX"

    def test_route_label_when_missing(self) -> None:
        from jetset.display import route_label

        flight = Flight(callsign="UAL2337")
        assert route_label(flight) == ""


class TestMetricsLabel:
    def test_metrics_label_defaults_to_page_0(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        assert metrics_label(flight) == "35000ft"

    def test_metrics_label_empty_when_no_data(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337")
        assert metrics_label(flight) == ""

    def test_page_0_shows_altitude(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        label = metrics_label(flight, page=0)
        assert label == "35000ft"

    def test_page_1_shows_speed(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        label = metrics_label(flight, page=1)
        assert label == "450kn"

    def test_page_2_shows_vertical_rate(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", vertical_rate=1500)
        label = metrics_label(flight, page=2)
        assert label == "▲1500ft/min"

    def test_page_2_descending_shows_down_arrow(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="SWA450", vertical_rate=-1200)
        label = metrics_label(flight, page=2)
        assert label == "▼1200ft/min"

    def test_page_2_level_flight(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", vertical_rate=0)
        label = metrics_label(flight, page=2)
        assert label == "▬0ft/min"

    def test_page_3_shows_track(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", track=270)
        label = metrics_label(flight, page=3)
        assert label == "270°W"

    def test_track_format_as_int(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(callsign="UAL2337", track=280.12)
        label = metrics_label(flight, page=3)
        assert label == "280°W"

    def test_four_pages_rotates(self) -> None:
        from jetset.display import metrics_label

        flight = Flight(
            callsign="UAL2337",
            altitude=35000, speed=450,
            vertical_rate=1500, track=270,
        )
        labels = [metrics_label(flight, page=i) for i in range(4)]
        assert len(set(labels)) == 4  # all different
