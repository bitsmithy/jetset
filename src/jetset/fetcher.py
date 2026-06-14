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

    COMMERCIAL_AIRCRAFT_TYPES = {
        "A319",
        "A320",
        "A321",
        "A21N",
        "A332",
        "A333",
        "A339",
        "A35K",
        "A388",
        "B38M",
        "B39M",
        "B737",
        "B738",
        "B739",
        "B744",
        "B748",
        "B752",
        "B753",
        "B762",
        "B763",
        "B764",
        "B772",
        "B773",
        "B77W",
        "B77L",
        "B778",
        "B779",
        "B787",
        "B788",
        "B789",
        "B78X",
        "BCS3",
        "CRJ2",
        "CRJ7",
        "CRJ9",
        "E75L",
        "E75S",
        "E190",
        "E195",
        "E170",
        "E175",
    }

    @staticmethod
    def _is_commercial(aircraft: dict) -> bool:
        callsign = (aircraft.get("flight") or "").strip()
        if not callsign:
            return False
        # If we know the aircraft type, it must be a recognised commercial type
        ac_type = aircraft.get("t")
        if ac_type and ac_type not in AdsbLolAdapter.COMMERCIAL_AIRCRAFT_TYPES:
            return False
        # Airline callsigns are 3-letter ICAO prefix + digits (e.g. "UAL2337")
        return (
            len(callsign) >= 4
            and callsign[:3].isalpha()
            and callsign[:3].isupper()
            and callsign[3:].isdigit()
        )

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
                        a for a in data["ac"]
                        if self._is_commercial(a) and self._is_airborne(a)
                    ]
                    display = airborne[:5]
                    self._enrich_routes(display)

                    if raw:
                        return display
                    elif display:
                        return [self.json_to_flight(f) for f in display]

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"[{type(self).__name__}] Error fetching nearby flights: {e}")

        return flights
