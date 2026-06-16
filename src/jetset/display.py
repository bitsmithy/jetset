"""Display formatting functions for flight cards on the LED panel."""

from jetset.models import Flight

_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _cardinal(track: float) -> str:
    """Nearest 8-point compass direction for a heading in degrees."""
    return _COMPASS[int(track / 45 + 0.5) % 8]


def loading_label(page: int = 0) -> str:
    if page == 1:
        return "LOADING."
    if page == 2:
        return "LOADING.."
    if page == 3:
        return "LOADING..."

    return "LOADING"


def flight_label(flight: Flight) -> str:
    """Format the callsign display string."""
    return flight.callsign


def aircraft_label(flight: Flight) -> str:
    """Format the aircraft type display string."""
    return flight.aircraft if flight.aircraft else ""


def route_label(flight: Flight) -> str:
    """Format the origin→destination route string."""
    return (
        f"{flight.route.origin.iata_code}\u2192{flight.route.destination.iata_code}"
        if flight.route
        else ""
    )


def metrics_label(flight: Flight, page: int = 0) -> str:
    """Format one metric page for the flight card.

    Pages:
        0 = altitude (e.g. "35K ft")
        1 = speed (e.g. "450 kt")
        2 = vertical rate (e.g. "1500▲ ft/m" or "LVL")
        3 = track (e.g. "270°")

    Returns an empty string if the relevant field is missing.
    """
    data = ""
    if page == 0 and flight.altitude:
        data += f"{flight.altitude} ft"
    elif page == 1 and flight.speed:
        data += f"{flight.speed} kt"
    elif page == 2 and flight.vertical_rate is not None:
        if flight.vertical_rate == 0:
            data += "LVL"
        else:
            formatted_rate = str(abs(flight.vertical_rate))
            if flight.vertical_rate > 0:
                formatted_rate += "\u25b2"
            elif flight.vertical_rate < 0:
                formatted_rate += "\u25bc"
            data += f"{formatted_rate} ft/m"
    elif page == 3 and flight.track is not None:
        data += f"{int(flight.track)}\u00b0 {_cardinal(flight.track)}"

    return data
