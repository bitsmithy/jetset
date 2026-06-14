"""Tests for the Flight model."""

from jetset.models import Flight


class TestFlightLabel:
    def test_airline_and_flight_number_from_callsign(self) -> None:
        flight = Flight(callsign="UAL2337")
        assert flight.airline == "UAL"
        assert flight.flight_number == "2337"
        assert flight.flight_label() == "UAL2337"

    def test_route_label_when_both_set(self) -> None:
        flight = Flight(callsign="UAL2337", origin="SFO", destination="LAX")
        assert flight.route_label() == "SFO→LAX"

    def test_route_label_when_missing(self) -> None:
        flight = Flight(callsign="UAL2337")
        assert flight.route_label() == ""


class TestMetricsLabel:
    def test_metrics_label_defaults_to_page_0(self) -> None:
        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        assert flight.metrics_label() == "35K ft"

    def test_metrics_label_empty_when_no_data(self) -> None:
        flight = Flight(callsign="UAL2337")
        assert flight.metrics_label() == ""


class TestMetricsCycling:
    def test_page_0_shows_altitude(self) -> None:
        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        label = flight.metrics_label(page=0)
        assert label == "35K ft"

    def test_page_1_shows_speed(self) -> None:
        flight = Flight(callsign="UAL2337", altitude=35000, speed=450)
        label = flight.metrics_label(page=1)
        assert label == "450 kt"

    def test_page_2_shows_vertical_rate(self) -> None:
        flight = Flight(callsign="UAL2337", vertical_rate=1500)
        label = flight.metrics_label(page=2)
        assert label == "1500▲ ft/m"

    def test_page_2_descending_shows_down_arrow(self) -> None:
        flight = Flight(callsign="SWA450", vertical_rate=-1200)
        label = flight.metrics_label(page=2)
        assert label == "1200▼ ft/m"

    def test_page_2_level_flight(self) -> None:
        flight = Flight(callsign="UAL2337", vertical_rate=0)
        label = flight.metrics_label(page=2)
        assert label == "LVL"

    def test_page_3_shows_track(self) -> None:
        flight = Flight(callsign="UAL2337", track=270)
        label = flight.metrics_label(page=3)
        assert label == "270°"

    def test_track_format_as_int(self) -> None:
        flight = Flight(callsign="UAL2337", track=280.12)
        label = flight.metrics_label(page=3)
        assert label == "280°"

    def test_four_pages_rotates(self) -> None:
        flight = Flight(
            callsign="UAL2337",
            altitude=35000, speed=450,
            vertical_rate=1500, track=270,
        )
        labels = [flight.metrics_label(page=i) for i in range(4)]
        assert len(set(labels)) == 4  # all different


class TestFlightBuffer:
    def test_push_and_retrieve(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer(maxlen=3)
        f1 = Flight(callsign="UAL2337")
        buf.push(f1)
        assert len(buf) == 1
        assert buf.flights == [f1]

    def test_deduplicates_by_callsign(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer(maxlen=3)
        buf.push(Flight(callsign="UAL2337"))
        buf.push(Flight(callsign="UAL2337"))
        assert len(buf) == 1

    def test_respects_maxlen(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer(maxlen=2)
        buf.push(Flight(callsign="UAL2337"))
        buf.push(Flight(callsign="AAL100"))
        buf.push(Flight(callsign="SWA450"))
        assert len(buf) == 2
        assert buf.flights[0].callsign == "AAL100"
        assert buf.flights[1].callsign == "SWA450"
