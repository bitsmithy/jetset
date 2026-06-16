#!/usr/bin/env python3
"""Compare route sources against AeroAPI (ground truth).

Pulls nearby flights through the normal app pipeline (so the "ours" column is
exactly what the app would display), then for up to 5 callsigns queries:
  - adsbdb (ours, free)   - what the app shows today
  - AirLabs (free)        - candidate free source (1000 calls/month)
  - AeroAPI (paid, truth) - authoritative, the column to trust
  - hexdb.io (free)       - reference cross-check

AeroAPI costs money (~$0.05/call), so it is OPT-IN: by default this runs free
sources only. Pass --truth to add the AeroAPI ground-truth column and the two
✓/✗ scores (adsbdb and AirLabs vs AeroAPI). Hard-capped at 5 callsigns.

Provide keys via the environment or a .env file:
    AIRLABS_API_KEY (optional, free signup)   AEROAPI_KEY (only for --truth)
Run:
    uv run python scripts/route-compare.py            # free sources only
    uv run python scripts/route-compare.py --truth    # adds paid AeroAPI

Codes: adsbdb / AirLabs / AeroAPI report IATA (IAH); hexdb.io reports ICAO.
"""

import os
import sys

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is a convenience; env vars work without it
    load_dotenv = None

from jetset.config import AppConfig
from jetset.fetcher import AdsbLolAdapter
from jetset.http import RequestsAPI

MAX_CALLSIGNS = 5  # AeroAPI is ~$0.05/call — cap the cost per run
AEROAPI_COST = 0.05
TIMEOUT = 10
AEROAPI_BASE = "https://aeroapi.flightaware.com/aeroapi"
AIRLABS_BASE = "https://airlabs.co/api/v9"
HEXDB_BASE = "https://hexdb.io/api/v1"
MISSING = "—"
NO_KEY = "no key"


def our_route(flight) -> str:
    if flight.route:
        return f"{flight.route.origin.iata_code}→{flight.route.destination.iata_code}"
    return MISSING


def aeroapi_route(api: RequestsAPI, callsign: str) -> str:
    """Authoritative origin→dest (IATA) for the in-progress flight, if any."""
    try:
        resp = api.get(f"/flights/{callsign}", timeout=TIMEOUT)
        resp.raise_for_status()
        flights = resp.json().get("flights", [])
        if not flights:
            return MISSING

        # Prefer the flight currently in the air; fall back to most recent.
        airborne = [
            f for f in flights
            if f.get("progress_percent") not in (None, 0, 100) and not f.get("cancelled")
        ]
        flight = (airborne or flights)[0]

        def code(end: str) -> str:
            obj = flight.get(end) or {}
            return obj.get("code_iata") or obj.get("code_icao") or obj.get("code") or "?"

        return f"{code('origin')}→{code('destination')}"
    except (requests.RequestException, ValueError) as e:
        return f"error: {e}"


def airlabs_route(api: RequestsAPI, callsign: str, key: str) -> str:
    """Origin→dest (IATA) from AirLabs' real-time flights data, if available."""
    try:
        resp = api.get(
            "/flights", params={"flight_icao": callsign, "api_key": key}, timeout=TIMEOUT
        )
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, dict) and body.get("error"):
            return f"error: {body['error'].get('code', 'api error')}"
        flights = body.get("response") or []
        flight = flights[0] if isinstance(flights, list) and flights else None
        if not isinstance(flight, dict):
            return MISSING
        dep = flight.get("dep_iata") or flight.get("dep_icao")
        arr = flight.get("arr_iata") or flight.get("arr_icao")
        if not dep and not arr:
            return MISSING
        return f"{dep or '?'}→{arr or '?'}"
    except (requests.RequestException, ValueError) as e:
        return f"error: {e}"


def hexdb_route(api: RequestsAPI, callsign: str) -> str:
    """Origin→dest (ICAO) from hexdb.io's crowd-sourced route data."""
    try:
        resp = api.get(f"/route/icao/{callsign}", timeout=TIMEOUT)
        if resp.status_code == 404:
            return MISSING
        resp.raise_for_status()
        route = resp.json().get("route", "")
        legs = route.split("-") if route else []
        if len(legs) < 2:
            return MISSING
        return f"{legs[0]}→{legs[-1]}"
    except (requests.RequestException, ValueError) as e:
        return f"error: {e}"


def agree(candidate: str, truth: str) -> str:
    """Score a candidate route against the ground-truth route."""
    if truth in (MISSING, NO_KEY) or truth.startswith("error"):
        return "?"  # no ground truth to compare against
    if candidate in (MISSING, NO_KEY) or candidate.startswith("error"):
        return "·"  # candidate offered no route
    return "✓" if candidate == truth else "✗"


def render_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> None:
    widths = [max(len(str(r[i])) for r in [*rows, headers]) for i in range(len(headers))]

    def line(row: tuple[str, ...]) -> str:
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row))

    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def main() -> None:
    if load_dotenv is not None:
        load_dotenv()  # load API keys from a .env file if present

    # AeroAPI costs money, so it is opt-in only. Default run uses free sources.
    use_truth = "--truth" in sys.argv
    truth_key = os.environ.get("AEROAPI_KEY")
    if use_truth and not truth_key:
        print("--truth needs AEROAPI_KEY (AeroAPI is ~$0.05/call).", file=sys.stderr)
        sys.exit(1)

    airlabs_key = os.environ.get("AIRLABS_API_KEY")
    if not airlabs_key:
        print("(AIRLABS_API_KEY not set — AirLabs column will be blank)", file=sys.stderr)

    config = AppConfig.load(os.environ.get("JETSET_CONFIG"))
    adapter = AdsbLolAdapter()
    flights = adapter.nearby_flights(config.home_lat, config.home_lon, config.range)
    flights = [f for f in flights if f.callsign][:MAX_CALLSIGNS]

    if not flights:
        print("No nearby flights with routes right now — try again later.")
        return

    if use_truth:
        cost = len(flights) * AEROAPI_COST
        print(f"Comparing {len(flights)} callsign(s) — AeroAPI cost ~${cost:.2f}\n")
    else:
        print(
            f"{len(flights)} callsign(s), free sources only — "
            "pass --truth to add AeroAPI (~$0.05/callsign)\n"
        )

    airlabs = RequestsAPI(base_url=AIRLABS_BASE)
    hexdb = RequestsAPI(base_url=HEXDB_BASE)
    aero = None
    if use_truth:
        aero = RequestsAPI(base_url=AEROAPI_BASE, headers={"x-apikey": truth_key})

    rows = []
    for flight in flights:
        ours = our_route(flight)
        air = airlabs_route(airlabs, flight.callsign, airlabs_key) if airlabs_key else NO_KEY
        hex_route = hexdb_route(hexdb, flight.callsign)
        if use_truth:
            truth = aeroapi_route(aero, flight.callsign)
            rows.append(
                (flight.callsign, ours, air, truth, hex_route,
                 agree(ours, truth), agree(air, truth))
            )
        else:
            rows.append((flight.callsign, ours, air, hex_route))

    if use_truth:
        render_table(
            rows, ("Callsign", "adsbdb", "AirLabs", "AeroAPI*", "hexdb.io", "ours✓", "AirLabs✓")
        )
        print("\n* AeroAPI = ground truth.  ✓ correct  ✗ wrong  · no route  ? no truth")
    else:
        render_table(rows, ("Callsign", "adsbdb", "AirLabs", "hexdb.io"))
    print("Codes: adsbdb/AirLabs/AeroAPI = IATA; hexdb.io = ICAO.")


if __name__ == "__main__":
    main()
