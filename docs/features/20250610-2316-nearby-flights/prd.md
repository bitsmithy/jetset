# Nearby Flights — PRD

## Problem Statement

I want to see live aircraft flying near my home displayed on a 64×32 LED matrix panel. The display should feel like a miniature airport departure board — cycling through nearby flights with their airline, flight number, route, altitude, and speed. When no flights are nearby, I still want to see recent flights that passed through.

## Solution

A Python application that periodically fetches nearby aircraft from a flight tracking API, renders each flight as a card on the LED matrix, and cycles through them. The display uses a dot-matrix aesthetic with a pixel font (5×7 BDF bitmap) to match the departure-board feel. The flight data source is swappable — the application talks to an abstract interface, with concrete adapters for each provider. The first adapter targets FlightAware AeroAPI.

## User Stories

1. As a Jetset owner, I want the display to show the airline and flight number of a nearby flight, along with the airline's logo, so that I can identify which airline is overhead.
2. As a Jetset owner, I want the display to show the origin and destination airports of a flight, so that I can see where the plane is coming from and going to.
3. As a Jetset owner, I want the display to show the aircraft type (e.g., B738, A320), so that I can recognise the model of plane.
4. As a Jetset owner, I want the display to show altitude and speed of a flight, so that I can see how fast and high it's travelling.
5. As a Jetset owner, I want the display to cycle through all nearby flights every few seconds, so that I can see what's overhead without staring at a static list.
6. As a Jetset owner, I want the display to show a history of the last few flights when no aircraft are currently in range, so that the display is never blank.
7. As a Jetset owner, I want to configure my home location (latitude/longitude) and tracking range in a config file, so that I can set it up for my location.
8. As a Jetset owner, I want to configure how often flight data is refreshed and how long each flight is shown, so that I can tune the pacing to my preference.
9. As a developer, I want the flight data source to be swappable via an abstract interface, so that I can add support for other APIs (FlightAware, ADSB‑exchange, etc.) without changing the rest of the system.
10. As a developer, I want adapters to handle API errors gracefully (timeouts, rate limits, network failures), so that the display continues working even when the API is unreachable.
11. As a Jetset owner, I want the display to use a pixel font (Departure Mono) that evokes airport departure boards, so that the visual matches the theme.
12. As a developer, I want tests for the flight model, the API interface, and data source adapters, so that I can verify core logic without the hardware.

## Implementation Decisions

### Flight API Interface

A protocol/ABC with a single method: `nearby_flights(lat, lon, range_mi, raw=False) -> Sequence[Flight]`. The main loop receives the configured adapter via dependency injection — it never imports an adapter directly. When `raw=True`, the adapter returns the full API response dict for fixture capture.

The `Flight` data class is the shared contract between adapters and the renderer. All adapters normalise their API responses into this shape.

### AeroAPI Adapter

The first adapter targets FlightAware AeroAPI (`https://aeroapi.flightaware.com/aeroapi`). Authentication is via `x-apikey` header using an API key from the `AEROAPI_API_KEY` environment variable (loaded from `.env` via `python-dotenv`).

Queries the `/flights/search` endpoint with `-latlong` bounding box query. Response is JSON with a `flights` array. Each flight object includes `ident`, `origin`/`destination` objects, `aircraft_type`, and `last_position` (altitude, groundspeed, heading).

Key conversions:
- **altitude**: AeroAPI returns hundreds of feet → stored as feet (×100)
- **groundspeed**: already in knots, stored as-is
- **heading**: degrees (0–360), stored in the `track` field
- **vertical_rate**: not currently populated (AeroAPI only has `altitude_change` as C/D/-)

The adapter catches `requests.exceptions.RequestException` and `ValueError` (for JSON decode failures) and returns an empty list — the display loop never crashes from a fetch failure.

### Flight Model

`Flight` is an immutable dataclass with fields: callsign, aircraft, origin, destination, altitude, speed, track, vertical_rate. Display helpers (`flight_label`, `route_label`, `metrics_label`) derive formatted strings from the fields.

`FlightBuffer` is a fixed-size ring buffer (default 5) of recent flights. It deduplicates by callsign — the same flight won't be pushed twice. Used to populate the empty state display.

### Renderer

The 5×7 BDF bitmap font (from hzeller's rpi-rgb-led-matrix) is rendered directly via `graphics.DrawText` on the matrix canvas. No Pillow or off-screen compositing — text is drawn pixel by pixel directly onto the canvas.

Flight card layout (4 rows of 5×7 pixels each):
- Row 0: Airline + flight number (e.g., `UAL2337`)
- Row 1: Origin → destination (e.g., `SFO→LAX`)
- Row 2: Aircraft type (e.g., `B738`)
- Row 3: Metrics page (ALT/SPD/TRK/VRT cycling every 3s)

### Airline Logos

Airline logos are sourced from the github.com/sexym0nk3y/airline-logos repository (993 PNGs, 90×90 each, indexed by ICAO airline code). A setup script downloads and caches the logos locally. During rendering, the logo for the current flight's airline code is downscaled to ~20×16 px and blitted pixel-by-pixel into the top-right corner of the flight card. Logos that don't exist locally are silently skipped — the display still works without them.

### Display Abstraction

The matrix creation is behind a helper that tries `RGBMatrixEmulator` first, then `rgbmatrix`. This lets the same code run on the emulator during development and on real hardware on the Pi with zero changes.

### Configuration

A single `config.yaml` file with sections for `home` (lat, lon, range_mi), `display` (cols, rows, cycle_sec, refresh_sec), and `api` (source, credentials). The config loader returns a frozen dataclass — parsed once at startup.

### Empty State

When no flights are currently in range, the display shows recent flights from the history buffer. If the buffer is also empty (first run), a static "NO DATA" message is shown.

## Testing Decisions

Tests verify behavior, not implementation. A good test for this codebase exercises an external interface (the Flight API protocol, a Flight dataclass method, the FlightBuffer ring buffer) with real inputs and asserts on visible outputs — never on internal state or private helpers.

The following modules will have dedicated test files:

- **Flight Model** — construction, display label formatting, edge cases (missing fields, long strings)
- **Flight API interface** — test that the protocol enforces the expected contract (a mock adapter passes, a class missing the method fails)
- **OpenSky Adapter** — parse real OpenSky state vectors into Flight objects, handle partial/malformed data, handle API errors gracefully

Testing the renderer and display abstraction is deferred — they require the emulator or hardware, and the visual output is best validated by eye.

## Out of Scope

- **Tracked/followed flight** — selecting a specific flight to follow exclusively is a future feature
- **Audio alerts** — no beeps, chimes, or announcements
- **Web dashboard** — no HTTP UI beyond the emulator's built-in viewer
- **Historical trends** — storing flight data for later analysis
- **Multiple panel chains** — chaining more than one 64×32 panel is deferred
- **ADS-B receiver integration** — only cloud APIs for now
- **Mobile app or remote control** — no external input beyond the config file

## Further Notes

- AeroAPI is a paid per-query API with a free tier ($5/month free usage, $10/month for ADS-B feeders). The default refresh interval of 30 seconds keeps usage within the free tier.
- The 5×7 BDF font is from hzeller's rpi-rgb-led-matrix repository, licensed under the Apache License 2.0.
