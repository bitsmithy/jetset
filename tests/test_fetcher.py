"""Tests for the flight API interface and AeroAPI adapter."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from jetset.models import Flight

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "aeroapi_response.json"


@runtime_checkable
class FlightAPI(Protocol):
    """Protocol for flight data sources."""

    def nearby_flights(  # noqa: E501
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]:
        ...


class TestFlightAPIProtocol:
    def test_protocol_accepts_valid_adapter(self) -> None:
        from jetset.fetcher import AeroAPIAdapter

        assert isinstance(AeroAPIAdapter("test-key"), FlightAPI)


AEROAPI_FLIGHT_EXAMPLE = {
    "ident": "UAL2337",
    "ident_icao": "UAL2337",
    "ident_iata": "UA2337",
    "fa_flight_id": "string",
    "registration": "N12345",
    "origin": {
        "code": "KSFO",
        "code_icao": "KSFO",
        "code_iata": "SFO",
        "timezone": "America/Los_Angeles",
        "name": "San Francisco International",
        "city": "San Francisco",
    },
    "destination": {
        "code": "KLAX",
        "code_icao": "KLAX",
        "code_iata": "LAX",
        "timezone": "America/Los_Angeles",
        "name": "Los Angeles International",
        "city": "Los Angeles",
    },
    "aircraft_type": "B738",
    "last_position": {
        "altitude": 350,
        "altitude_change": "C",
        "groundspeed": 450,
        "heading": 270.0,
        "latitude": 37.6,
        "longitude": -122.4,
        "timestamp": "2026-06-12T19:59:59Z",
    },
}


class TestAeroAPIFlightToFlight:
    def test_parses_complete_aeroapi_flight(self) -> None:
        from jetset.fetcher import AeroAPIAdapter

        flight = AeroAPIAdapter.json_to_flight(AEROAPI_FLIGHT_EXAMPLE)

        assert flight.callsign == "UAL2337"
        assert flight.origin == "KSFO"
        assert flight.destination == "KLAX"
        assert flight.aircraft == "B738"
        assert flight.altitude == 35000
        assert flight.speed == 450
        assert flight.track == 270.0
        assert flight.vertical_rate is None

    def test_parses_all_fixture_flights(self) -> None:
        from jetset.fetcher import AeroAPIAdapter

        fixture = json.loads(FIXTURE_PATH.read_text())
        for flight_data in fixture["flights"]:
            flight = AeroAPIAdapter.json_to_flight(flight_data)
            assert flight.callsign
            # altitude=None is valid (no position data); speed=0 is valid (on ground)
            assert isinstance(flight.altitude, (int, type(None)))
            assert isinstance(flight.speed, (int, type(None)))
            assert isinstance(flight.track, (float, int, type(None)))
            assert flight.vertical_rate is None

    def test_missing_last_position_returns_defaults(self) -> None:
        from jetset.fetcher import AeroAPIAdapter

        data = {"ident": "SWA45"}
        flight = AeroAPIAdapter.json_to_flight(data)

        assert flight.callsign == "SWA45"
        assert flight.altitude is None
        assert flight.speed is None
        assert flight.track is None
        assert flight.vertical_rate is None


class TestAeroAPIFetchNearby:
    def test_returns_flights_from_mocked_response(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AeroAPIAdapter

        fixture = json.loads(FIXTURE_PATH.read_text())

        adapter = AeroAPIAdapter("test-key")
        with patch.object(adapter._api, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: fixture)
            flights = adapter.nearby_flights(37.6, -122.4, 80)

        assert len(flights) >= 1
        assert all(f.callsign for f in flights)
        assert all(f.origin for f in flights)
        assert all(f.destination for f in flights)

    def test_handles_http_error_gracefully(self) -> None:
        from unittest.mock import patch

        import requests

        from jetset.fetcher import AeroAPIAdapter

        adapter = AeroAPIAdapter("test-key")
        error = requests.exceptions.RequestException("API error")
        with patch.object(adapter._api, "get", side_effect=error):
            flights = adapter.nearby_flights(37.6, -122.4, 80)

        assert flights == []

    def test_returns_empty_list_when_no_flights_in_range(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AeroAPIAdapter

        mock_response = {
            "flights": [],
            "num_pages": 0,
            "links": {"next": ""},
        }

        adapter = AeroAPIAdapter("test-key")
        with patch.object(adapter._api, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)
            flights = adapter.nearby_flights(37.6, -122.4, 80)

        assert flights == []

    def test_raw_returns_full_response(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AeroAPIAdapter

        fixture = json.loads(FIXTURE_PATH.read_text())

        adapter = AeroAPIAdapter("test-key")
        with patch.object(adapter._api, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: fixture)
            data = adapter.nearby_flights(37.6, -122.4, 80, raw=True)

        assert "flights" in data
        assert len(data["flights"]) >= 1
