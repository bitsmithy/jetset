from collections import namedtuple
from collections.abc import Sequence
from typing import Any, Protocol

import requests

from jetset.models import Flight

BoundingBox = namedtuple("BoundingBox", "lat_min lat_max lon_min lon_max")


def bounding_box(lat: float, lon: float, range: int) -> BoundingBox:
    delta = range / 111  # ~1° ≈ 111km, so range / 111 gives the half-range in degrees

    return BoundingBox(lat - delta, lat + delta, lon - delta, lon + delta)


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

    def _enrich_routes(self, flight_data: list[Any]):
        callsigns = [d.get("flight", "").rstrip() for d in flight_data]
        unique_callsigns = list({c for c in callsigns})
        route_map = {}

        try:
            with self._route_api as api:
                for c in unique_callsigns:
                    if route_data := api.get(f"/callsign/{c}").json():
                        route_resp = route_data.get("response", {})
                        if isinstance(route_resp, dict):
                            route = route_resp.get("flightroute", {})
                            origin = route.get("origin", {}).get("iata_code")
                            destination = route.get("destination", {}).get("iata_code")
                            route_map[c] = {"origin": origin, "destination": destination}

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error enriching routes: {e}")

        for d in flight_data:
            callsign = d.get("flight", "").rstrip()
            d["origin"] = route_map.get(callsign, {}).get("origin")
            d["destination"] = route_map.get(callsign, {}).get("destination")

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
                    self._enrich_routes(data["ac"])

                    if raw:
                        return data["ac"]
                    elif raw_flights := data["ac"]:
                        return [self.json_to_flight(f) for f in raw_flights]

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error fetching nearby flights: {e}")

        return flights


class AeroAPIAdapter(FlightAPI):
    def __init__(self, api_key: str) -> None:
        self._api = RequestsAPI(
            "https://aeroapi.flightaware.com/aeroapi", headers={"x-apikey": api_key}
        )

    @staticmethod
    def json_to_flight(data: dict) -> Flight:
        origin = (data.get("origin") or {}).get("code_iata")
        destination = (data.get("destination") or {}).get("code_iata")
        callsign = data.get("ident", "")
        aircraft = data.get("aircraft_type")

        last_pos = data.get("last_position", {})
        raw_altitude = last_pos.get("altitude")
        altitude = raw_altitude * 100 if raw_altitude else None
        speed = last_pos.get("groundspeed")
        heading = last_pos.get("heading")  # This is lossy, AeroAPI only has heading, not track

        return Flight(
            callsign=callsign,
            origin=origin,
            destination=destination,
            aircraft=aircraft,
            altitude=altitude,
            speed=speed,
            track=heading,
        )

    def nearby_flights(
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]:
        bb = bounding_box(lat, lon, range)
        flights = []

        try:
            with self._api as api:
                data = api.get(
                    "/flights/search",
                    params={
                        "query": f'-latlong "{bb.lat_min} {bb.lon_min} {bb.lat_max} {bb.lon_max}"'
                    },
                )

                if raw:
                    return data.json()
                elif raw_flights := data.json()["flights"]:
                    return [self.json_to_flight(f) for f in raw_flights]

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error fetching nearby flights: {e}")

        return flights
