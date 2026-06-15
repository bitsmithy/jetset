import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import requests

from jetset.http import RequestsAPI
from jetset.models import Airport, Flight, FlightRoute, Position

logger = logging.getLogger(__name__)


class RouteCache:
    @dataclass(frozen=True)
    class CacheEntry:
        timestamp: float
        route: FlightRoute

    def __init__(self, ttl: int = 900) -> None:
        self.cache: dict[str, self.CacheEntry] = {}
        self.ttl = ttl

    def get(self, callsign: str) -> FlightRoute | None:
        entry = self.cache.get(callsign)

        if entry:
            now = time.time()
            if now - entry.timestamp <= self.ttl:
                return entry.route

    def put(self, callsign: str, route: FlightRoute) -> None:
        self.cache[callsign] = self.CacheEntry(time.time(), route)

    def clear(self) -> None:
        self.cache = {}


class FlightAPI(Protocol):
    def nearby_flights(self, lat: float, lon: float, range: int, raw: bool) -> Sequence[Flight]: ...


class AdsbLolAdapter(FlightAPI):
    def __init__(self) -> None:
        self._flight_api = RequestsAPI("https://api.adsb.lol/v2")
        self._route_api = RequestsAPI("https://api.adsbdb.com/v0")
        self._route_cache = RouteCache()

    def _fetch_route(self, callsign: str) -> FlightRoute | None:
        try:
            with self._route_api as api:
                logger.debug("Fetching route for callsign %s", callsign)
                if route_data := api.get(f"/callsign/{callsign}").json():
                    route_resp = route_data.get("response", {})
                    if isinstance(route_resp, dict):
                        route = route_resp.get("flightroute", {})
                        origin = Airport(
                            route.get("origin", {}).get("iata_code"),
                            Position(
                                route.get("origin", {}).get("latitude"),
                                route.get("origin", {}).get("longitude"),
                            ),
                        )
                        destination = Airport(
                            route.get("destination", {}).get("iata_code"),
                            Position(
                                route.get("destination", {}).get("latitude"),
                                route.get("destination", {}).get("longitude"),
                            ),
                        )

                        return FlightRoute(origin, destination)
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning("Error fetching route for callsign %s: %s", callsign, e)

    def _enrich_routes(self, flight_data: list[Any], max_flights: int = 5, max_xtd: float = 100):
        enriched = []

        for d in flight_data:
            if len(enriched) >= max_flights:
                break
            callsign = d.get("flight", "").rstrip()
            if not callsign:
                continue

            route = self._route_cache.get(callsign)
            if route is None:
                aircraft_track = d.get("track", 0)
                aircraft_position = Position(d.get("lat", 0), d.get("lon", 0))
                route = self._fetch_route(callsign)
                if route and route.plausible(aircraft_track, aircraft_position, max_xtd):
                    self._route_cache.put(callsign, route)
                else:
                    route = None

            if route is not None:
                enriched.append({**d, "route": route})

        return enriched

    @staticmethod
    def _is_airborne(aircraft: dict) -> bool:
        alt = aircraft.get("alt_baro")
        if alt is None or alt == "ground":
            return False
        return int(alt) > 0

    @staticmethod
    def json_to_flight(data: dict) -> Flight:
        route = data.get("route")
        callsign = data.get("flight", "").rstrip()
        aircraft = data.get("t")
        altitude = data.get("alt_baro")
        speed = int(data.get("gs", 0)) if data.get("gs") else None
        track = data.get("track")
        vrate = data.get("baro_rate")

        return Flight(
            callsign=callsign,
            route=route,
            aircraft=aircraft,
            altitude=altitude,
            speed=speed,
            track=track,
            vertical_rate=vrate,
        )

    def nearby_flights(
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]:
        flights = []
        range_nm = range / 1.852  # km -> nautical miles
        try:
            with self._flight_api as api:
                logger.debug(
                    "Fetching nearby flights at (%.4f, %.4f) within %d NM", lat, lon, range_nm
                )
                if data := api.get(f"/point/{lat}/{lon}/{range_nm}").json():
                    airborne = [a for a in data["ac"] if self._is_airborne(a)]
                    enriched = self._enrich_routes(airborne, max_flights=5, max_xtd=range_nm)

                    if raw:
                        return enriched
                    elif enriched:
                        return [self.json_to_flight(f) for f in enriched]

        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning("Error fetching nearby flights: %s", e)

        return flights
