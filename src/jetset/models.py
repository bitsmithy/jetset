import logging
from collections import deque
from dataclasses import dataclass

from jetset import geo
from jetset.geo import Position

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Flight:
    callsign: str
    aircraft: str | None = None
    route: FlightRoute | None = None
    altitude: int | None = None
    speed: int | None = None
    track: float | None = None
    vertical_rate: int | None = None

    def __post_init__(self) -> None:
        logger.debug(
            "Flight(callsign=%s, aircraft=%s, origin=%s, "
            "destination=%s, altitude=%s, speed=%s, track=%s, "
            "vertical_rate=%s)",
            self.callsign,
            self.aircraft,
            self.route.origin.iata_code if self.route else None,
            self.route.destination.iata_code if self.route else None,
            self.altitude,
            self.speed,
            self.track,
            self.vertical_rate,
        )

    @property
    def airline(self) -> str:
        return self.callsign[:3] if self.callsign else ""

    @property
    def flight_number(self) -> str:
        return self.callsign[3:] if self.callsign else ""


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

    def replace(self, callsign: str, flight: Flight) -> None:
        for i, existing in enumerate(self._flights):
            if existing.callsign == callsign:
                self._flights[i] = flight
                return


@dataclass(frozen=True)
class Airport:
    iata_code: str
    position: Position


@dataclass(frozen=True)
class FlightRoute:
    origin: Airport
    destination: Airport

    def __post_init__(self) -> None:
        logger.debug(
            "FlightRoute(origin=%s, destination=%s)",
            self.origin.iata_code,
            self.destination.iata_code,
        )

    @property
    def bearing(self) -> float:
        """Great-circle bearing from origin to destination (0–360°)."""
        return geo.bearing(self.origin.position, self.destination.position)

    @property
    def distance(self) -> float:
        """Great-circle distance from origin to destination in NM."""
        return geo.distance(self.origin.position, self.destination.position)

    def cross_track_distance(self, aircraft_position: Position) -> float:
        """Perpendicular distance from aircraft to this route's great-circle path in NM."""
        return geo.cross_track_distance(
            self.origin.position, self.destination.position, aircraft_position
        )

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
