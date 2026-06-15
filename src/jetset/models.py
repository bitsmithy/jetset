import math
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    callsign: str
    aircraft: str | None = None
    route: FlightRoute | None = None
    altitude: int | None = None
    speed: int | None = None
    track: float | None = None
    vertical_rate: int | None = None

    @property
    def airline(self) -> str:
        return self.callsign[:3] if self.callsign else ""

    @property
    def flight_number(self) -> str:
        return self.callsign[3:] if self.callsign else ""

    def flight_label(self) -> str:
        return f"{self.callsign}"

    def aircraft_label(self) -> str:
        return self.aircraft if self.aircraft else ""

    def route_label(self) -> str:
        return (
            f"{self.route.origin.iata_code}→{self.route.destination.iata_code}"
            if self.route
            else ""
        )

    def metrics_label(self, page: int = 0) -> str:
        data = ""
        if page == 0 and self.altitude:
            formatted_altitude = f"{self.altitude // 1000}K"
            data += f"{formatted_altitude} ft"
        elif page == 1 and self.speed:
            data += f"{self.speed} kt"
        elif page == 2 and self.vertical_rate is not None:
            if self.vertical_rate == 0:
                data += "LVL"
            else:
                formatted_rate = str(abs(self.vertical_rate))
                if self.vertical_rate > 0:
                    formatted_rate += "▲"
                elif self.vertical_rate < 0:
                    formatted_rate += "▼"
                data += f"{formatted_rate} ft/m"
        elif page == 3 and self.track is not None:
            data += f"{int(self.track)}°"

        return data


class FlightBuffer:
    def __init__(self, maxlen=5):
        self._flights: deque[Flight] = deque(maxlen=maxlen)

    def __len__(self) -> int:
        return len(self._flights)

    @property
    def flights(self) -> list[Flight]:
        return list(self._flights)

    def push(self, flight: Flight) -> None:
        for existing in self._flights:
            if existing.callsign == flight.callsign:
                return

        self._flights.append(flight)


@dataclass(frozen=True)
class Airport:
    iata_code: str
    position: Position


@dataclass(frozen=True)
class Position:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class FlightRoute:
    origin: Airport
    destination: Airport

    EARTH_RADIUS = 3440.065  # in nautical miles

    @property
    def bearing(self) -> float:
        """Calculate initial great-circle bearing from origin to destination
        Aviation formula:
            θ = atan2(sin(Δlon)·cos(lat2), cos(lat1)·sin(lat2) − sin(lat1)·cos(lat2)·cos(Δlon))

        Returns bearing in degrees (0–360), where 0 = north, 90 = east, etc.
        """
        lat1_rad = math.radians(self.origin.position.latitude)
        lat2_rad = math.radians(self.destination.position.latitude)
        d_lon_rad = math.radians(
            self.destination.position.longitude - self.origin.position.longitude
        )

        x = math.sin(d_lon_rad) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
            lat2_rad
        ) * math.cos(d_lon_rad)

        angle_rad = math.atan2(x, y)
        bearing = math.degrees(angle_rad)
        return (bearing + 360) % 360

    @property
    def distance(self) -> float:
        """Great-circle distance from origin to destination in nautical miles.

        Uses the haversine formula:
            a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
            c = 2·atan2(√a, √(1−a))
            distance = c · R

        where R = 3440 NM (Earth's mean radius in nautical miles), φ is
        latitude, λ is longitude, Δ is the difference between origin and
        destination.

        Returns:
            Distance along the great-circle route in nautical miles.
        """

        lat1_rad = math.radians(self.origin.position.latitude)
        lat2_rad = math.radians(self.destination.position.latitude)
        d_lat_rad = math.radians(self.destination.position.latitude - self.origin.position.latitude)
        d_lon_rad = math.radians(
            self.destination.position.longitude - self.origin.position.longitude
        )

        haversine = (
            math.sin(d_lat_rad / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon_rad / 2) ** 2
        )
        central_angle_rad = 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))
        return central_angle_rad * self.EARTH_RADIUS

    def cross_track_distance(self, aircraft_position: Position) -> float:
        """Perpendicular distance from the aircraft to this route's great-circle path.

        An aircraft may be heading in the right direction (bearing check passes)
        but be geographically far from the route — e.g., a plane near IAH is
        300 NM off the PHX→SFO great-circle line even if both happen to share
        a similar bearing.

        This is the cross-track component of the along-track/cross-track
        decomposition:
            xtd = asin(sin(d / R) · sin(θ_ac − θ_ab)) · R

        where d is the distance from origin to aircraft, θ_ac is the bearing
        from origin to aircraft, and θ_ab is the route bearing.

        Args:
            aircraft_position: The aircraft's current position.

        Returns:
            Distance in nautical miles from the aircraft to the great-circle
            line connecting origin and destination. Always non-negative.
        """
        aircraft_vector = FlightRoute(self.origin, Airport("_", aircraft_position))

        dist_ac = aircraft_vector.distance
        bearing_ac = aircraft_vector.bearing

        xtd = math.asin(
            math.sin(dist_ac / self.EARTH_RADIUS)
            * math.sin(math.radians(bearing_ac - self.bearing))
        )
        return abs(xtd * self.EARTH_RADIUS)

    def plausible(self, aircraft_track: float, aircraft_position: Position, max_xtd: float) -> bool:
        """Check if an aircraft is plausibly flying this route.

        Two checks are applied:

        1. **Bearing alignment** — the aircraft's track must be within 60°
           of the great-circle bearing from origin to destination. This
           rejects stale schedule data where the route doesn't match the
           aircraft's heading.

        2. **Cross-track distance** — the aircraft must be within
           `max_xtd` nautical miles of the great-circle path. This
           rejects routes that pass the bearing check but are
           geographically far from the aircraft.

        For example, a flight near Houston tracking 140° is likely
        IAH→BOG (bearing ~138°), not LAX→ITO (bearing ~256°).

        Args:
            aircraft_track: The aircraft's current heading in degrees (0–360).
            aircraft_position: The aircraft's current position.
            max_xtd: Maximum allowable cross-track distance in nautical miles.
                Typically the user's configured range.

        Returns:
            True if both checks pass, False otherwise.
        """
        diff = abs(aircraft_track - self.bearing)
        if min(diff, 360 - diff) > 60:
            return False

        if self.cross_track_distance(aircraft_position) > max_xtd:
            return False

        return True
