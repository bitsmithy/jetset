from collections.abc import Sequence
from typing import Any, Protocol

import requests

from jetset.models import Airport, Flight, FlightRoute, Position


class RequestsAPI(requests.Session):
    def __init__(
        self, base_url: str | None = None, headers: dict[str, str] | None = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

        if headers:
            self.headers.update(headers)

    def request(self, method, url, *args, **kwargs):
        if self.base_url:
            url: str = self.base_url.rstrip("/") + url

        return super().request(method, url, *args, **kwargs)


class FlightAPI(Protocol):
    def nearby_flights(self, lat: float, lon: float, range: int, raw: bool) -> Sequence[Flight]: ...


class AdsbLolAdapter(FlightAPI):
    def __init__(self) -> None:
        self._flight_api = RequestsAPI("https://api.adsb.lol/v2")
        self._route_api = RequestsAPI("https://api.adsbdb.com/v0")

    def _fetch_route(self, callsign: str) -> FlightRoute | None:
        try:
            with self._route_api as api:
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
            print(f"[{type(self).__name__}] Error fetching route for callsign {callsign}: {e}")

    def _enrich_routes(self, flight_data: list[Any], max_flights: int = 5, max_xtd: float = 100):
        route_map: dict[str, FlightRoute] = {}
        enriched = []
        seen: set[str] = set()

        for d in flight_data:
            if len(enriched) >= max_flights:
                break
            callsign = d.get("flight", "").rstrip()
            if not callsign:
                continue

            if callsign in seen:
                d["route"] = route_map[callsign]
                enriched.append(d)
            else:
                seen.add(callsign)
                if route := self._fetch_route(callsign):
                    aircraft_track = d.get("track", 0)
                    aircraft_position = Position(d.get("lat", 0), d.get("lon", 0))
                    if route.plausible(aircraft_track, aircraft_position, max_xtd):
                        route_map[callsign] = route
                        d["route"] = route
                        enriched.append(d)

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
                if data := api.get(f"/point/{lat}/{lon}/{range_nm}").json():
                    airborne = [a for a in data["ac"] if self._is_airborne(a)]
                    enriched = self._enrich_routes(airborne, max_flights=5, max_xtd=range_nm)

                    if raw:
                        return enriched
                    elif enriched:
                        return [self.json_to_flight(f) for f in enriched]

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error fetching nearby flights: {e}")

        return flights
