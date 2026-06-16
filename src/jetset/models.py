import logging
from dataclasses import dataclass

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
    """Holds the flights captured by the most recent fetch.

    A fetch captures all nearby flights at once and replaces the buffer
    wholesale, so a plain list is all that's needed — no bounded deque,
    incremental push, or dedup. The display slides a window across the flights.
    """

    def __init__(self) -> None:
        self._flights: list[Flight] = []

    def __len__(self) -> int:
        return len(self._flights)

    @property
    def flights(self) -> list[Flight]:
        return list(self._flights)

    def set_all(self, flights) -> None:
        """Replace the buffer with a fresh batch of flights."""
        self._flights = list(flights)


@dataclass(frozen=True)
class Airport:
    iata_code: str


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
