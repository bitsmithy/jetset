import logging
import math
import os
from collections.abc import Sequence
from typing import Protocol

import requests

from jetset.http import RequestsAPI
from jetset.models import Airport, Flight, FlightRoute

ROUTE_TIMEOUT = 10  # seconds; AirLabs lookups must not hang the fetch
NM_PER_DEGREE = 60.0

logger = logging.getLogger(__name__)


class FlightAPI(Protocol):
    def nearby_flights(
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]: ...


def _meters_to_feet(meters: float | None) -> int | None:
    return round(meters * 3.28084) if meters is not None else None


def _kmh_to_knots(kmh: float | None) -> int | None:
    return round(kmh / 1.852) if kmh else None


def _ms_to_ft_per_min(ms: float | None) -> int | None:
    return round(ms * 196.850394) if ms is not None else None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AirLabsAdapter(FlightAPI):
    """Single data source for the display.

    One AirLabs ``/flights?bbox=`` call returns every nearby flight with its
    metrics AND route, so it replaces the former adsb.lol + adsbdb + hexdb +
    plausibility-filter stack (see README's "Data source history"). The
    1000-requests/month free tier is honoured by the app's long refresh
    interval — one bbox call per refresh.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api = RequestsAPI("https://airlabs.co/api/v9")
        self._api_key = api_key or os.environ.get("AIRLABS_API_KEY")

    @staticmethod
    def _bbox(lat: float, lon: float, range_nm: float) -> str:
        """AirLabs bbox 'min_lat,min_lon,max_lat,max_lon' covering the range."""
        half_lat = range_nm / NM_PER_DEGREE
        half_lon = range_nm / (NM_PER_DEGREE * max(math.cos(math.radians(lat)), 0.1))
        return f"{lat - half_lat},{lon - half_lon},{lat + half_lat},{lon + half_lon}"

    @staticmethod
    def to_flight(data: dict) -> Flight:
        """Map an AirLabs flight (metric units) to a Flight (feet/knots/ft-min)."""
        dep, arr = data.get("dep_iata"), data.get("arr_iata")
        route = FlightRoute(Airport(dep), Airport(arr)) if dep and arr else None
        return Flight(
            callsign=(data.get("flight_icao") or "").strip(),
            aircraft=data.get("aircraft_icao"),
            route=route,
            altitude=_meters_to_feet(data.get("alt")),
            speed=_kmh_to_knots(data.get("speed")),
            track=float(data.get("dir")) if data.get("dir") is not None else None,
            vertical_rate=_ms_to_ft_per_min(data.get("v_speed")),
        )

    def nearby_flights(
        self, lat: float, lon: float, range: int, raw: bool = False
    ) -> Sequence[Flight]:
        if not self._api_key:
            logger.warning("AIRLABS_API_KEY not set; cannot fetch flights")
            return []
        range_nm = range / 1.852  # km -> nautical miles
        try:
            with self._api as api:
                logger.debug("Fetching AirLabs flights near (%.4f, %.4f)", lat, lon)
                body = api.get(
                    "/flights",
                    params={"bbox": self._bbox(lat, lon, range_nm), "api_key": self._api_key},
                    timeout=ROUTE_TIMEOUT,
                ).json()
            if not isinstance(body, dict) or body.get("error"):
                detail = body.get("error") if isinstance(body, dict) else body
                logger.warning("AirLabs returned no usable data: %s", detail)
                return []
            raw_flights = [
                f
                for f in (body.get("response") or [])
                if f.get("flight_icao") and f.get("status") == "en-route"
            ]
            # Sort by proximity to home so the display shows the closest
            # flights first. Flights without coordinates go to the end.
            raw_flights.sort(
                key=lambda f: _haversine_km(lat, lon, f.get("lat", 0), f.get("lng", 0))
                if f.get("lat") is not None and f.get("lng") is not None
                else float("inf")
            )
            if raw:
                return raw_flights
            return [self.to_flight(f) for f in raw_flights]
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning("Error fetching flights from AirLabs: %s", e)
            return []
