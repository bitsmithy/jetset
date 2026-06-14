"""Tests for the flight API interface and adapters."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from jetset.models import Flight

ADSB_LOL_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "adsblol_response.json"


@runtime_checkable
class FlightAPI(Protocol):
    """Protocol for flight data sources."""

    def nearby_flights(  # noqa: E501
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]:
        ...


class TestFlightAPIProtocol:
    def test_protocol_accepts_valid_adapter(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        assert isinstance(AdsbLolAdapter(), FlightAPI)





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

    def test_filters_ga_aircraft(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        ga = {"flight": "N12345", "t": "C172"}
        commercial = {"flight": "UAL2337 ", "t": "B738"}
        no_callsign = {"t": "B738"}

        assert not AdsbLolAdapter._is_commercial(ga)
        assert AdsbLolAdapter._is_commercial(commercial)
        assert not AdsbLolAdapter._is_commercial(no_callsign)

        # 3-letter callsign with a GA type should be rejected
        trf_p28a = {"flight": "TRF558", "t": "P28A"}
        assert not AdsbLolAdapter._is_commercial(trf_p28a)

    def test_airborne_filter(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        airborne = {"flight": "UAL2337", "alt_baro": 35000}
        on_ground = {"flight": "SWA45", "alt_baro": 0}
        grounded_str = {"flight": "AAL100", "alt_baro": "ground"}
        no_alt = {"flight": "DAL200", "t": "B738"}

        assert AdsbLolAdapter._is_airborne(airborne)
        assert not AdsbLolAdapter._is_airborne(on_ground)
        assert not AdsbLolAdapter._is_airborne(grounded_str)
        assert not AdsbLolAdapter._is_airborne(no_alt)


def _make_adsblol_response() -> dict:
    return {
        "ac": [dict(ADSB_LOL_AIRCRAFT)],
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
        mock_flight.json.return_value = _make_adsblol_response()

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

    def test_raw_returns_enriched_commercial_dicts(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()

        mock_flight = MagicMock()
        mock_flight.json.return_value = _make_adsblol_response()

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._flight_api, "get", return_value=mock_flight), \
                patch.object(adapter._route_api, "get", return_value=mock_route):
            data = adapter.nearby_flights(37.6, -122.4, 80, raw=True)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["flight"] == "UAL1170 "
        # raw mode returns filtered + enriched dicts
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
