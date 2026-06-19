"""Display formatting functions for flight cards on the LED panel."""

from pathlib import Path

from PIL import Image

from jetset.models import Flight

_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Vertical-rate markers: filled triangles for climb/descend, a bar for level.
_CLIMB, _DESCEND, _LEVEL = "▲", "▼", "▬"


def _cardinal(track: float) -> str:
    """Nearest 8-point compass direction for a heading in degrees."""
    return _COMPASS[int(track / 45 + 0.5) % 8]


def load_logo(airline_code: str, logo_dir: Path) -> Image.Image | None:
    """Load the airline logo for a given ICAO airline code from logo_dir.

    Looks for {airline_code}.png in logo_dir. Returns the image unchanged
    (caller is responsible for scaling and blitting). Returns None if the file
    doesn't exist or can't be opened.
    """
    path = logo_dir / f"{airline_code}.png"
    try:
        return Image.open(path)
    except FileNotFoundError, PermissionError:
        return None


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
        0 = altitude (e.g. "35000ft")
        1 = speed (e.g. "450kn")
        2 = vertical rate (e.g. "▲1500ft/min", "▼1200ft/min", or "▬0ft/min")
        3 = track (e.g. "270°W")
        4 = distance from home (e.g. "32km away")

    Returns an empty string if the relevant field is missing.
    """
    data = ""
    if page == 0 and flight.altitude:
        data += f"{flight.altitude}ft"
    elif page == 1 and flight.speed:
        data += f"{flight.speed}kn"
    elif page == 2 and flight.vertical_rate is not None:
        rate = flight.vertical_rate
        if rate > 0:
            marker = _CLIMB
        elif rate < 0:
            marker = _DESCEND
        else:
            marker = _LEVEL
        data += f"{marker}{abs(rate)}ft/min"
    elif page == 3 and flight.track is not None:
        data += f"{int(flight.track)}°{_cardinal(flight.track)}"
    elif page == 4 and flight.distance_km is not None:
        data += f"{round(flight.distance_km)}km away"

    return data
