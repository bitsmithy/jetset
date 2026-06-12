# Nearby Flights — Tasks

Source PRD: [prd.md](./prd.md)

## Slice 1: Flight Model + hardcoded flight card

**Type:** AFK
**Blocked by:** None — can start immediately
**User stories covered:** 1, 2, 3, 4, 11

### What to build

The core data types (`Flight` dataclass, `FlightBuffer` ring buffer) and a renderer that draws flight cards on the matrix canvas using the Departure Mono font. Start with a hardcoded `Flight` instance so the end-to-end path is demoable from the first slice: model → render → display.

The Departure Mono OTF font is downloaded and rendered via Pillow at the appropriate pixel size for the 64×32 display. Text is composited onto an off-screen PIL image, then blitted pixel-by-pixel onto the matrix canvas. The flight card layout shows airline + flight number, origin → destination, aircraft type, and metrics (altitude, speed, vertical rate) in the standard colour hierarchy.

### Acceptance criteria

- [ ] `Flight` dataclass exists with all fields and display helpers (`flight_label`, `route_label`, `metrics_label`)
- [ ] `FlightBuffer` ring buffer deduplicates by callsign and respects max length
- [ ] Departure Mono font is rendered correctly at legible pixel size on the 64×32 canvas
- [ ] `uv run jetset` shows a hardcoded flight card on the emulator at http://localhost:8888/
- [ ] `uv run ruff check src/` passes
- [ ] `uv run pytest -v` passes for model tests

---

## Slice 2: Config + Flight API Protocol + AeroAPI adapter

**Type:** AFK
**Blocked by:** Slice 1 (model is needed as the return type)
**User stories covered:** 7, 9, 10

### What to build

The `config.yaml` loader that reads home coordinates, range, display timing, and API settings into frozen dataclasses. The abstract Flight API interface (protocol class with a `nearby_flights` method). The first concrete adapter for FlightAware AeroAPI, which queries the `/flights/search` endpoint with a bounding box derived from the configured home and range.

The adapter maps AeroAPI flight JSON into `Flight` objects (origin/destination/aircraft/altitude/speed/track), converts altitude from hundreds of feet to feet, and handles network errors gracefully (returning an empty list on failure).

### Acceptance criteria

- [x] Config loader reads `config.yaml` and returns frozen dataclasses with sensible defaults
- [x] Flight API protocol defines `nearby_flights` with correct signature
- [x] AeroAPI adapter implements the protocol and returns parsed `Flight` objects
- [x] Adapter handles HTTP errors and JSON decode errors without crashing
- [x] Tests verify the API interface contract, JSON-to-Flight conversion, and error handling
- [x] `save_fixtures.py` script + `make fixtures` target for real API response fixtures
- [x] API key via `AEROAPI_API_KEY` env var (loaded from `.env` via python-dotenv)
- [x] `uv run ruff check src/` passes
- [x] `uv run pytest -v` passes for all tests

**Status:** ✅ Complete

---

## Slice 3: Main loop integration

**Type:** AFK
**Blocked by:** Slice 2 (needs adapter + config), Slice 1 (needs renderer + model)
**User stories covered:** 5, 7, 8

### What to build

The main loop that orchestrates the full pipeline: fetch nearby flights via the configured adapter → cycle through them at the configured interval → render each flight card → swap to the display. The loop runs at ~20 fps with periodic fetch cycles (every 30 seconds by default). Graceful shutdown on SIGINT/SIGTERM.

The display abstraction (try `RGBMatrixEmulator` first, fall back to real `rgbmatrix`) is already part of the scaffold.

### Acceptance criteria

- [ ] Main loop fetches flights, cycles through them, and renders each card
- [ ] Cycling respects the configured `cycle_sec` interval
- [ ] Fetch respects the configured `refresh_sec` interval
- [ ] Graceful shutdown on Ctrl+C (SIGINT/SIGTERM)
- [ ] Display abstraction correctly falls back through emulator → real hardware
- [ ] `uv run jetset` shows real nearby flight cards cycling on the emulator

---

## Slice 4: Empty state + flight history

**Type:** AFK
**Blocked by:** Slice 3 (needs working main loop)
**User stories covered:** 6

### What to build

When the fetch returns no flights (nothing in range), the display shows recent flights from the `FlightBuffer` history instead of going blank. The buffer is populated during normal operation as flights come and go. If the buffer is empty (first ever run), a static "NO DATA" message is shown.

The history buffer size is configurable via config.yaml (default 5).

### Acceptance criteria

- [ ] Display shows recent flights from history when no flights are currently in range
- [ ] History buffer populates automatically during normal fetch cycles
- [ ] Static "NO DATA" message shown when buffer is also empty
- [ ] History buffer size is configurable in config.yaml

---

## Slice 5: Airline logos

**Type:** AFK
**Blocked by:** Slice 3 (needs working flight display), Slice 1 (needs renderer)
**User stories covered:** 1

### What to build

A setup script that downloads airline logos from the github.com/sexym0nk3y/airline-logos repository (993 PNGs, 90×90 each, indexed by ICAO airline code). Logos are cached locally. During rendering, the logo for the current flight's airline code is loaded, downscaled to ~20×16 px, and blitted into the top-right corner of the flight card. Missing logos are silently skipped.

### Acceptance criteria

- [ ] Setup script downloads and caches airline logos locally
- [ ] Logo appears in the top-right corner of the flight card for recognised airlines
- [ ] Display still works correctly for airlines without a cached logo (silent skip)
- [ ] `uv run ruff check src/` passes
