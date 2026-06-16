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

    def refresh_flight(self, flight: Flight) -> Flight | None: ...


class TestFlightAPIProtocol:
    def test_protocol_accepts_valid_adapter(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        assert isinstance(AdsbLolAdapter(), FlightAPI)





ADSB_LOL_AIRCRAFT = {
    "flight": "UAL1170 ",
    "t": "B772",
    "alt_baro": 17700,
    "gs": 400.3,
    "track": 140.0,
    "baro_rate": 1600,
    "lat": 33.568214,
    "lon": -119.232388,
    "r": "N771UA",
    "category": "A5",
}

ADSBDB_RESPONSE = {
    "response": {
        "flightroute": {
            "origin": {"iata_code": "SFO", "latitude": 37.62, "longitude": -122.38},
            "destination": {"iata_code": "LAX", "latitude": 33.94, "longitude": -118.41},
        }
    },
}


class TestAdsbLolFlightToFlight:
    def test_converts_enriched_aircraft(self) -> None:
        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport, FlightRoute, Position

        aircraft = dict(ADSB_LOL_AIRCRAFT)
        aircraft["route"] = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )

        flight = AdsbLolAdapter.json_to_flight(aircraft)

        assert flight.callsign == "UAL1170"
        assert flight.aircraft == "B772"
        assert flight.altitude == 17700
        assert flight.speed == 400
        assert flight.track == 140.0
        assert flight.vertical_rate == 1600
        assert flight.route.origin.iata_code == "SFO"
        assert flight.route.destination.iata_code == "LAX"

    def test_enrich_routes_adds_origin_destination(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()
        aircraft_list = [dict(ADSB_LOL_AIRCRAFT)]

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._route_api, "get", return_value=mock_route):
            result = adapter._enrich_routes(aircraft_list)

        assert len(result) == 1
        assert result[0]["route"].origin.iata_code == "SFO"
        assert result[0]["route"].destination.iata_code == "LAX"

    def test_enrich_routes_stops_after_max_flights(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()
        # Two aircraft with different callsigns
        ac1 = dict(ADSB_LOL_AIRCRAFT)  # UAL1170
        ac2 = dict(ADSB_LOL_AIRCRAFT)
        ac2["flight"] = "SWA4186"

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._route_api, "get", return_value=mock_route) as mock_get:
            # max_flights=1 so it should stop after the first successful enrich
            result = adapter._enrich_routes([ac1, ac2], max_flights=1)

        # Only one flight should be enriched
        assert len(result) == 1
        assert result[0]["route"].origin.iata_code == "SFO"
        # API should only have been called once
        assert mock_get.call_count == 1



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


class TestDistance:
    def test_distance_iah_to_bog(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        route = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )
        # IAH -> BOG ≈ 1936 NM
        assert round(route.distance) == 1936

    def test_distance_zero(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        route = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("IAH", Position(29.99, -95.34)),
        )
        assert route.distance == 0.0


class TestBearing:
    def test_bearing_north_to_south(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        origin = Airport("NPL", Position(0.0, 0.0))
        destination = Airport("SPL", Position(-10.0, 0.0))
        route = FlightRoute(origin, destination)

        assert route.bearing == 180.0


class TestCrossTrackDistance:
    def test_aircraft_at_origin_zero_cross_track(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        route = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )
        xtd = route.cross_track_distance(Position(29.99, -95.34))
        assert round(xtd) == 0

    def test_aircraft_near_iah_is_off_phx_sfo_route(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        # PHX (33.43, -112.02) -> SFO (37.62, -122.38)
        route = FlightRoute(
            Airport("PHX", Position(33.43, -112.02)),
            Airport("SFO", Position(37.62, -122.38)),
        )
        # Aircraft near IAH (29.99, -95.34) — ~300 NM off this route
        xtd = route.cross_track_distance(Position(29.99, -95.34))
        assert 250 < xtd < 350


class TestRoutePlausible:
    def test_track_aligned_with_route_bearing(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        iah_bog = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )
        # Aircraft at origin — cross-track = 0, always passes
        assert iah_bog.plausible(140.0, Position(29.99, -95.34), 100)

    def test_track_opposite_route_rejected(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        iah_bog = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )

        assert not iah_bog.plausible(10.0, Position(29.99, -95.34), 100)

    def test_cross_track_rejects_off_route_aircraft(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        # PHX (33.43, -112.02) -> SFO (37.62, -122.38), bearing ~299°
        phx_sfo = FlightRoute(
            Airport("PHX", Position(33.43, -112.02)),
            Airport("SFO", Position(37.62, -122.38)),
        )
        # Aircraft near IAH heading 299° — passes bearing check but ~300 NM off
        assert not phx_sfo.plausible(299.0, Position(29.99, -95.34), 100)

    def test_cross_track_accepts_on_route_aircraft(self) -> None:
        from jetset.models import Airport, FlightRoute, Position

        iah_bog = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )
        # Aircraft near origin heading toward destination — well within 100 NM
        assert iah_bog.plausible(140.0, Position(29.99, -95.34), 100)

    def test_enrich_routes_rejects_implausible_route(self) -> None:
        from unittest.mock import patch

        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport, FlightRoute, Position

        adapter = AdsbLolAdapter()

        # Aircraft heading east (track 90°) over Texas
        aircraft = dict(ADSB_LOL_AIRCRAFT)
        aircraft["track"] = 90.0
        # Route LAX→ITO has bearing ~256° — 166° off track, should be rejected
        lax_ito = FlightRoute(
            Airport("LAX", Position(33.94, -118.41)),
            Airport("ITO", Position(19.72, -155.05)),
        )

        with patch.object(adapter, "_fetch_route", return_value=lax_ito):
            result = adapter._enrich_routes([aircraft])

        assert len(result) == 0
        assert "route" not in aircraft

    def test_enrich_routes_accepts_plausible_route(self) -> None:
        from unittest.mock import patch

        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport, FlightRoute, Position

        adapter = AdsbLolAdapter()

        # Aircraft heading ~140° (southeast) at IAH
        aircraft = dict(ADSB_LOL_AIRCRAFT)
        aircraft["track"] = 140.0
        aircraft["lat"] = 29.99
        aircraft["lon"] = -95.34
        # Route IAH→BOG has bearing ~138° — only 2° off, should be accepted
        iah_bog = FlightRoute(
            Airport("IAH", Position(29.99, -95.34)),
            Airport("BOG", Position(4.70, -74.15)),
        )

        with patch.object(adapter, "_fetch_route", return_value=iah_bog):
            result = adapter._enrich_routes([aircraft])

        assert len(result) == 1
        assert result[0]["route"].origin.iata_code == "IAH"

    def test_enrich_routes_respects_custom_range(self) -> None:
        from unittest.mock import patch

        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport, FlightRoute, Position

        adapter = AdsbLolAdapter()

        # Aircraft near LAX (33.57, -119.23) heading 140°
        # SFO→LAX has bearing ~138°, so bearing check passes.
        # Cross-track from aircraft to SFO→LAX is ~20 NM.
        aircraft = dict(ADSB_LOL_AIRCRAFT)
        aircraft["track"] = 140.0
        sfo_lax = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )

        with patch.object(adapter, "_fetch_route", return_value=sfo_lax):
            # max_xtd=5 NM — too tight, cross-track ~20 NM exceeds it
            tight = adapter._enrich_routes([dict(aircraft)], max_xtd=5)
            assert len(tight) == 0

            # max_xtd=50 NM — loose enough, aircraft ~20 NM off is accepted
            loose = adapter._enrich_routes([dict(aircraft)], max_xtd=50)
            assert len(loose) == 1


class TestAdsbLolFetchNearby:
    def test_passes_range_to_enrich_routes(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()

        mock_flight = MagicMock()
        mock_flight.json.return_value = _make_adsblol_response()

        with patch.object(adapter._flight_api, "get", return_value=mock_flight):
            with patch.object(adapter, "_enrich_routes", return_value=[]) as mock_enrich:
                adapter.nearby_flights(37.6, -122.4, 185)
                mock_enrich.assert_called_once()
                _, kwargs = mock_enrich.call_args
                assert round(kwargs.get("max_xtd")) == 100

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
            flights = adapter.nearby_flights(37.6, -122.4, 185)

        assert len(flights) == 1
        flight = flights[0]
        assert flight.callsign == "UAL1170"
        assert flight.route.origin.iata_code == "SFO"
        assert flight.route.destination.iata_code == "LAX"
        assert flight.aircraft == "B772"

    def test_raw_returns_enriched_dicts(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter

        adapter = AdsbLolAdapter()

        mock_flight = MagicMock()
        mock_flight.json.return_value = _make_adsblol_response()

        mock_route = MagicMock()
        mock_route.json.return_value = ADSBDB_RESPONSE

        with patch.object(adapter._flight_api, "get", return_value=mock_flight), \
                patch.object(adapter._route_api, "get", return_value=mock_route):
            data = adapter.nearby_flights(37.6, -122.4, 185, raw=True)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["flight"] == "UAL1170 "
        # raw mode returns filtered + enriched dicts
        assert data[0]["route"].origin.iata_code == "SFO"
        assert data[0]["route"].destination.iata_code == "LAX"


ADSB_LOL_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "adsblol_response.json"


class TestRefreshFlight:
    def test_returns_fresh_metrics_with_preserved_route(self) -> None:
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport, Flight, FlightRoute, Position

        adapter = AdsbLolAdapter()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ac": [dict(ADSB_LOL_AIRCRAFT)],
            "total": 1,
        }

        route = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )
        existing = Flight(
            callsign="UAL1170", route=route, altitude=35000,
            speed=450, track=140.0, vertical_rate=1600,
        )

        with patch.object(adapter._flight_api, "get", return_value=mock_resp):
            refreshed = adapter.refresh_flight(existing)

        assert refreshed is not None
        assert refreshed.callsign == "UAL1170"
        assert refreshed.altitude == 17700  # fresh from mock
        assert refreshed.speed == 400
        # Route should be preserved from the original
        assert refreshed.route is route

    def test_returns_original_when_no_aircraft_in_response(self) -> None:
        # The callsign endpoint can return valid JSON with an empty "ac" list
        # when the aircraft is no longer airborne; keep the stale flight.
        from unittest.mock import MagicMock, patch

        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Flight

        adapter = AdsbLolAdapter()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ac": [], "total": 0}
        existing = Flight(callsign="UCA4237", altitude=35000, speed=450)

        with patch.object(adapter._flight_api, "get", return_value=mock_resp):
            refreshed = adapter.refresh_flight(existing)

        assert refreshed is existing


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
            assert isinstance(flight.route, (type(None),))
            assert isinstance(flight.aircraft, (str, type(None)))

        # Fixture data has origin/destination string keys but not FlightRoute objects
        assert all(f.route is None for f in flights)


class TestParseAirport:
    def test_parses_valid_dict(self) -> None:
        from jetset.fetcher import AdsbLolAdapter
        from jetset.models import Airport

        data = {"iata_code": "SFO", "latitude": 37.62, "longitude": -122.38}
        result = AdsbLolAdapter._parse_airport(data)

        assert isinstance(result, Airport)
        assert result.iata_code == "SFO"
        assert result.position.latitude == 37.62
        assert result.position.longitude == -122.38

    def test_returns_none_when_missing_iata(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        data = {"latitude": 37.62, "longitude": -122.38}
        assert AdsbLolAdapter._parse_airport(data) is None

    def test_returns_none_when_missing_latitude(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        data = {"iata_code": "SFO", "longitude": -122.38}
        assert AdsbLolAdapter._parse_airport(data) is None

    def test_returns_none_when_missing_longitude(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        data = {"iata_code": "SFO", "latitude": 37.62}
        assert AdsbLolAdapter._parse_airport(data) is None

    def test_returns_none_for_empty_dict(self) -> None:
        from jetset.fetcher import AdsbLolAdapter

        assert AdsbLolAdapter._parse_airport({}) is None
