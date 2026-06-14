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
        assert flight.origin == "SFO"
        assert flight.destination == "LAX"
        assert flight.aircraft == "B738"
        assert flight.altitude == 35000
        assert flight.speed == 450
        assert flight.track == 270.0
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
        assert all(isinstance(f.origin, (str, type(None))) for f in flights)
        assert all(isinstance(f.destination, (str, type(None))) for f in flights)

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


class TestAeroAPIFixture:
    def test_parses_all_fixture_flights(self) -> None:
        from jetset.fetcher import AeroAPIAdapter

        fixture = json.loads(FIXTURE_PATH.read_text())
        assert len(fixture["flights"]) >= 1

        for flight_data in fixture["flights"]:
            flight = AeroAPIAdapter.json_to_flight(flight_data)
            assert flight.callsign
            assert isinstance(flight.altitude, (int, type(None)))
            assert isinstance(flight.speed, (int, type(None)))
            assert isinstance(flight.track, (float, int, type(None)))
            assert flight.vertical_rate is None
            assert isinstance(flight.origin, (str, type(None)))
            assert isinstance(flight.destination, (str, type(None)))


ADSB_LOL_AIRCRAFT = {
    "flight": "UAL1170 ",
    "t": "B772",
    "alt_baro": 17700,
    "gs": 400.3,
    "track": 223.79,
    "baro_rate": 1600,
    "lat": 33.568214,
    "lon": -119.232388,
    "r": "N771UA",
    "category": "A5",
}

ADSBDB_RESPONSE = {
    "response": {
        "flightroute": {
            "origin": {"iata_code": "SFO"},
            "destination": {"iata_code": "LAX"},
        }
    },
}


class TestAdsbLolFlightToFlight:
    def test_converts_enriched_aircraft(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        aircraft = dict(ADSB_LOL_AIRCRAFT)
        aircraft["origin"] = "SFO"
        aircraft["destination"] = "LAX"

        flight = AdsbLolAdapter.json_to_flight(aircraft)

        assert flight.callsign == "UAL1170"
        assert flight.aircraft == "B772"
        assert flight.altitude == 17700
        assert flight.speed == 400
        assert flight.track == 223.79
        assert flight.vertical_rate == 1600
        assert flight.origin == "SFO"
        assert flight.destination == "LAX"

    def test_enrich_routes_adds_origin_destination(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()
        aircraft_list = [dict(ADSB_LOL_AIRCRAFT)]

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._route_api, "get", return_value=mock_route):
            adapter._enrich_routes(aircraft_list)

        assert aircraft_list[0]["origin"] == "SFO"
        assert aircraft_list[0]["destination"] == "LAX"


ADSB_LOL_RESPONSE = {
    "ac": [ADSB_LOL_AIRCRAFT],
    "total": 1,
    "now": 1234567890,
    "msg": "No error",
    "ctime": 0,
    "ptime": 0,
}


class TestAdsbLolFetchNearby:
    def test_returns_flights_from_mocked_response(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()

        mock_flight = MagicMock()
        mock_flight.json.return_value = ADSB_LOL_RESPONSE

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._flight_api, "get", return_value=mock_flight), \
                patch.object(adapter._route_api, "get", return_value=mock_route):
            flights = adapter.nearby_flights(37.6, -122.4, 80)

        assert len(flights) == 1
        flight = flights[0]
        assert flight.callsign == "UAL1170"
        assert flight.origin == "SFO"
        assert flight.destination == "LAX"
        assert flight.aircraft == "B772"

    def test_raw_returns_enriched_dicts(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()

        mock_flight = MagicMock()
        mock_flight.json.return_value = ADSB_LOL_RESPONSE

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._flight_api, "get", return_value=mock_flight), \
                patch.object(adapter._route_api, "get", return_value=mock_route):
            data = adapter.nearby_flights(37.6, -122.4, 80, raw=True)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["flight"] == "UAL1170 "
        assert data[0]["origin"] == "SFO"
        assert data[0]["destination"] == "LAX"


ADSB_LOL_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "adsblol_response.json"


class TestAdsbLolFixture:
    def test_parses_all_fixture_flights(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        fixture = json.loads(ADSB_LOL_FIXTURE_PATH.read_text())
        assert len(fixture) >= 1

        flights = [AdsbLolAdapter.json_to_flight(f) for f in fixture]

        assert len(flights) == len(fixture)
        for flight in flights:
            # callsign can be empty if aircraft had no flight field
            assert isinstance(flight.callsign, str)
            assert isinstance(flight.altitude, (int, type(None)))
            assert isinstance(flight.speed, (int, type(None)))
            assert isinstance(flight.track, (float, type(None)))
            assert isinstance(flight.vertical_rate, (int, type(None)))
            assert isinstance(flight.origin, (str, type(None)))
            assert isinstance(flight.destination, (str, type(None)))
            assert isinstance(flight.aircraft, (str, type(None)))

        # At least some flights have enriched routes
        assert any(f.origin for f in flights)
        assert any(f.destination for f in flights)
