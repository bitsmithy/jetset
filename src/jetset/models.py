from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    callsign: str
    aircraft: str | None = None
    origin: str | None = None
    destination: str | None = None
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
        return f"{self.origin}→{self.destination}" if self.origin and self.destination else ""

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
