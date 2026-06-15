"""Tests for the RouteCache."""

from unittest.mock import patch

from jetset.fetcher import AdsbLolAdapter, RouteCache
from jetset.geo import Position
from jetset.models import Airport, FlightRoute

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


class TestRouteCache:
    def test_returns_route_after_put(self) -> None:
        cache = RouteCache()
        route = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )

        cache.put("UAL1170", route)
        result = cache.get("UAL1170")

        assert result is route

    def test_returns_none_for_missing(self) -> None:
        cache = RouteCache()
        assert cache.get("NONEXIST") is None

    def test_expired_entry_returns_none(self) -> None:
        cache = RouteCache(ttl=60)
        route = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )

        with patch("jetset.fetcher.time.time") as mock_time:
            mock_time.return_value = 1000.0
            cache.put("UAL1170", route)

            mock_time.return_value = 1061.0  # 61 seconds later
            result = cache.get("UAL1170")

        assert result is None

    def test_clear_removes_all_entries(self) -> None:
        cache = RouteCache()
        route = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )

        cache.put("UAL1170", route)
        cache.clear()

        assert cache.get("UAL1170") is None


class TestAdapterCacheIntegration:
    def test_uses_cached_route_without_api_call(self) -> None:
        adapter = AdsbLolAdapter()
        route = FlightRoute(
            Airport("SFO", Position(37.62, -122.38)),
            Airport("LAX", Position(33.94, -118.41)),
        )
        adapter._route_cache.put("UAL1170", route)

        aircraft = dict(ADSB_LOL_AIRCRAFT)

        with patch.object(adapter, "_fetch_route") as mock_fetch:
            result = adapter._enrich_routes([aircraft])

        assert len(result) == 1
        assert result[0]["route"] is route
        mock_fetch.assert_not_called()

    def test_fetch_failure_does_not_enrich_nor_cache(self) -> None:
        adapter = AdsbLolAdapter()
        aircraft = dict(ADSB_LOL_AIRCRAFT)

        with patch.object(adapter, "_fetch_route", return_value=None):
            result = adapter._enrich_routes([aircraft])

        assert len(result) == 0
        # Nothing should have been cached for this callsign
        assert adapter._route_cache.get("UAL1170") is None
