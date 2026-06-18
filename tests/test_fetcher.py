"""Tests for the AirLabs flight adapter."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable
from unittest.mock import MagicMock, patch

from jetset.models import Flight

AIRLABS_FIXTURE = Path(__file__).parent / "fixtures" / "airlabs_response.json"


@runtime_checkable
class FlightAPI(Protocol):
    def nearby_flights(
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]: ...


class TestFlightAPIProtocol:
    def test_adapter_satisfies_protocol(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        assert isinstance(AirLabsAdapter(), FlightAPI)


AIRLABS_FLIGHT = {
    "flight_icao": "UAL1170",
    "aircraft_icao": "B772",
    "alt": 5559,       # meters  -> ~18238 ft
    "speed": 621,      # km/h    -> ~335 kn
    "dir": 140.0,      # degrees
    "v_speed": 0,      # m/s     -> 0 ft/min
    "dep_iata": "SFO",
    "arr_iata": "LAX",
    "status": "en-route",
}


class TestAirLabsAdapter:
    def test_to_flight_converts_units_and_route(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        flight = AirLabsAdapter.to_flight(dict(AIRLABS_FLIGHT))

        assert flight.callsign == "UAL1170"
        assert flight.aircraft == "B772"
        assert flight.altitude == 18238  # meters -> feet
        assert flight.speed == 335       # km/h -> knots
        assert flight.track == 140.0
        assert flight.vertical_rate == 0
        route = flight.route
        assert route is not None
        assert route.origin.iata_code == "SFO"
        assert route.destination.iata_code == "LAX"

    def test_to_flight_no_route_when_endpoints_missing(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        data = {k: v for k, v in AIRLABS_FLIGHT.items() if k not in ("dep_iata", "arr_iata")}
        assert AirLabsAdapter.to_flight(data).route is None

    def test_nearby_flights_parses_bbox_response(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        adapter = AirLabsAdapter()
        adapter._api_key = "test"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": [dict(AIRLABS_FLIGHT)]}

        with patch.object(adapter._api, "get", return_value=mock_resp):
            flights = adapter.nearby_flights(29.99, -95.34, 200)

        assert len(flights) == 1
        assert flights[0].callsign == "UAL1170"
        route = flights[0].route
        assert route is not None
        assert route.destination.iata_code == "LAX"

    def test_nearby_flights_raw_returns_dicts(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        adapter = AirLabsAdapter()
        adapter._api_key = "test"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": [dict(AIRLABS_FLIGHT)]}

        with patch.object(adapter._api, "get", return_value=mock_resp):
            data = adapter.nearby_flights(29.99, -95.34, 200, raw=True)

        assert data == [dict(AIRLABS_FLIGHT)]

    def test_nearby_flights_empty_without_key(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        adapter = AirLabsAdapter()
        adapter._api_key = None
        assert adapter.nearby_flights(29.99, -95.34, 200) == []

    def test_nearby_flights_handles_api_error(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        adapter = AirLabsAdapter()
        adapter._api_key = "test"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"code": "unknown_api_key"}}

        with patch.object(adapter._api, "get", return_value=mock_resp):
            assert adapter.nearby_flights(29.99, -95.34, 200) == []

    def test_nearby_flights_filters_out_non_enroute(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        adapter = AirLabsAdapter()
        adapter._api_key = "test"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": [
                dict(AIRLABS_FLIGHT),
                {**AIRLABS_FLIGHT, "flight_icao": "N12345", "status": "landed"},
                {**AIRLABS_FLIGHT, "flight_icao": "N67890", "status": "scheduled"},
            ]
        }

        with patch.object(adapter._api, "get", return_value=mock_resp):
            flights = adapter.nearby_flights(29.99, -95.34, 200)

        assert len(flights) == 1
        assert flights[0].callsign == "UAL1170"

    def test_bbox_covers_the_range(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        bbox = AirLabsAdapter._bbox(29.99, -95.34, 108.0)
        min_lat, min_lon, max_lat, max_lon = (float(x) for x in bbox.split(","))
        assert min_lat < 29.99 < max_lat
        assert min_lon < -95.34 < max_lon


class TestAirLabsFixture:
    def test_maps_all_fixture_flights(self) -> None:
        from jetset.fetcher import AirLabsAdapter

        fixture = json.loads(AIRLABS_FIXTURE.read_text())
        flights = [AirLabsAdapter.to_flight(f) for f in fixture]

        assert len(flights) == len(fixture)
        for flight in flights:
            assert isinstance(flight.callsign, str)
            # Real API can return None for some metric fields.
            assert isinstance(flight.altitude, (int, type(None)))
            assert isinstance(flight.speed, (int, type(None)))
            assert isinstance(flight.vertical_rate, (int, type(None)))
            # track is always cast to float in to_flight.
            assert isinstance(flight.track, float)
        # Real en-route flights from AirLabs all have dep/arr,
        # so every fixture flight should map a route.
        for flight in flights:
            assert flight.route is not None, f"Flight {flight.callsign} has no route"
            assert isinstance(flight.route.origin.iata_code, str)
            assert isinstance(flight.route.destination.iata_code, str)
