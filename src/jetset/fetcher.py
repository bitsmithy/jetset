from collections.abc import Sequence
from typing import Any, Protocol

import requests

from jetset.models import Flight


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

    def _enrich_routes(self, flight_data: list[Any], max_flights: int = 5):
        route_map: dict[str, dict[str, str | None]] = {}
        enriched = 0
        seen: set[str] = set()

        try:
            with self._route_api as api:
                for d in flight_data:
                    if enriched >= max_flights:
                        break
                    callsign = d.get("flight", "").rstrip()
                    if not callsign or callsign in seen:
                        continue
                    seen.add(callsign)

                    if route_data := api.get(f"/callsign/{callsign}").json():
                        route_resp = route_data.get("response", {})
                        if isinstance(route_resp, dict):
                            route = route_resp.get("flightroute", {})
                            origin = route.get("origin", {}).get("iata_code")
                            destination = route.get("destination", {}).get("iata_code")
                            if origin and destination:
                                route_map[callsign] = {"origin": origin, "destination": destination}
                                enriched += 1

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error enriching routes: {e}")

        for d in flight_data:
            callsign = d.get("flight", "").rstrip()
            if callsign in route_map:
                d["origin"] = route_map[callsign]["origin"]
                d["destination"] = route_map[callsign]["destination"]

    @staticmethod
    def _is_airborne(aircraft: dict) -> bool:
        alt = aircraft.get("alt_baro")
        if alt is None or alt == "ground":
            return False
        return int(alt) > 0

    @staticmethod
    def json_to_flight(data: dict) -> Flight:
        origin = data.get("origin")
        destination = data.get("destination")
        callsign = data.get("flight", "").rstrip()
        aircraft = data.get("t")
        altitude = data.get("alt_baro")
        speed = int(data.get("gs", 0)) if data.get("gs") else None
        track = data.get("track")
        vrate = data.get("baro_rate")

        return Flight(
            callsign=callsign,
            origin=origin,
            destination=destination,
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
                    airborne = [
                        a for a in data["ac"] if self._is_airborne(a)
                    ]
                    self._enrich_routes(airborne, max_flights=5)
                    display = [
                        a for a in airborne
                        if a.get("origin") and a.get("destination")
                    ]

                    if raw:
                        return display
                    elif display:
                        return [self.json_to_flight(f) for f in display]

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error fetching nearby flights: {e}")

        return flights
