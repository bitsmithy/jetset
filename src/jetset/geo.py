"""Geospatial calculations for aviation (great-circle bearing, distance,
cross-track distance).

All functions operate on Position dataclass instances and return results
in nautical miles or degrees.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    latitude: float
    longitude: float


EARTH_RADIUS = 3440.065  # nautical miles


def bearing(origin: Position, destination: Position) -> float:
    """Calculate initial great-circle bearing from origin to destination.

    Aviation formula:
        θ = atan2(sin(Δlon)·cos(lat2), cos(lat1)·sin(lat2) − sin(lat1)·cos(lat2)·cos(Δlon))

    Returns bearing in degrees (0–360), where 0 = north, 90 = east, etc.
    """
    lat1_rad = math.radians(origin.latitude)
    lat2_rad = math.radians(destination.latitude)
    d_lon_rad = math.radians(destination.longitude - origin.longitude)

    x = math.sin(d_lon_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
        lat2_rad
    ) * math.cos(d_lon_rad)

    angle_rad = math.atan2(x, y)
    result = math.degrees(angle_rad)
    return (result + 360) % 360


def distance(origin: Position, destination: Position) -> float:
    """Great-circle distance between two positions in nautical miles.

    Uses the haversine formula:
        a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
        c = 2·atan2(√a, √(1−a))
        d = c · R

    where R = 3440 NM (Earth's mean radius).
    """
    lat1_rad = math.radians(origin.latitude)
    lat2_rad = math.radians(destination.latitude)
    d_lat_rad = math.radians(destination.latitude - origin.latitude)
    d_lon_rad = math.radians(destination.longitude - origin.longitude)

    haversine = (
        math.sin(d_lat_rad / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon_rad / 2) ** 2
    )
    central_angle_rad = 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))
    return central_angle_rad * EARTH_RADIUS


def cross_track_distance(
    route_origin: Position, route_destination: Position, aircraft_position: Position
) -> float:
    """Perpendicular distance from an aircraft to a great-circle route.

    Given a route (origin → destination) and an aircraft position, returns
    how far off the great-circle path the aircraft is, in nautical miles.

    Uses the cross-track formula:
        xtd = asin(sin(d_ac / R) · sin(θ_ac − θ_route)) · R

    where d_ac is distance from route origin to aircraft and θ_ac is the
    bearing from route origin to aircraft.

    Returns a non-negative distance in NM.
    """
    d_ac = distance(route_origin, aircraft_position)
    # Bearing from route origin to aircraft
    bearing_ac = bearing(route_origin, aircraft_position)
    # Bearing of the route itself
    bearing_route = bearing(route_origin, route_destination)

    xtd = math.asin(
        math.sin(d_ac / EARTH_RADIUS) * math.sin(math.radians(bearing_ac - bearing_route))
    )
    return abs(xtd * EARTH_RADIUS)
