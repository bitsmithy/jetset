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
    def test_set_all_replaces_contents(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer()
        buf.set_all([Flight(callsign="UAL2337"), Flight(callsign="SWA45")])

        assert len(buf) == 2
        assert [f.callsign for f in buf.flights] == ["UAL2337", "SWA45"]

    def test_set_all_overwrites_previous_batch(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer()
        buf.set_all([Flight(callsign="UAL2337")])
        buf.set_all([Flight(callsign="AAL100"), Flight(callsign="SWA45")])

        assert [f.callsign for f in buf.flights] == ["AAL100", "SWA45"]

    def test_flights_returns_a_copy(self) -> None:
        from jetset.models import FlightBuffer

        buf = FlightBuffer()
        buf.set_all([Flight(callsign="UAL2337")])
        buf.flights.append(Flight(callsign="SWA45"))

        assert len(buf) == 1
