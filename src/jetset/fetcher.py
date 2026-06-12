from collections import namedtuple
from collections.abc import Sequence
from typing import Protocol

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


class AeroAPIAdapter(FlightAPI):
    def __init__(self, api_key: str) -> None:
        self._api = RequestsAPI(
            "https://aeroapi.flightaware.com/aeroapi", headers={"x-apikey": api_key}
        )

    @staticmethod
    def json_to_flight(data: dict) -> Flight:
        origin = data.get("origin", {}).get("code")
        destination = data.get("destination", {}).get("code")
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
