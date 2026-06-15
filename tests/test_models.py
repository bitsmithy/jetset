"""Tests for the Flight model."""

from jetset.models import Flight


class TestFlightLabel:
    def test_airline_and_flight_number_from_callsign(self) -> None:
        from jetset.display import flight_label

        flight = Flight(callsign="UAL2337")
        assert flight.airline == "UAL"
        assert flight.flight_number == "2337"
        assert flight_label(flight) == "UAL2337"

class TestFlightBuffer:
    def test_push_and_retrieve(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer(maxlen=3)
        f1 = Flight(callsign="UAL2337")
        buf.push(f1)
        assert len(buf) == 1
        assert buf.flights == [f1]

    def test_replace_updates_existing_flight_by_callsign(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer(maxlen=3)
        buf.push(Flight(callsign="UAL2337", altitude=35000))
        replacement = Flight(callsign="UAL2337", altitude=37000)

        buf.replace("UAL2337", replacement)

        assert len(buf) == 1
        assert buf.flights[0].altitude == 37000

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
