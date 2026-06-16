# Jetset

A live flight tracking LED display — shows aircraft flying near you on a 64×32 HUB75 matrix panel.

## Prerequisites

Everything is managed via `mise`:

```bash
mise install
```

This installs the toolchain versions pinned in `mise.toml`.

## Setup

```bash
uv sync
```

## Targets

| Command | What it does |
|---|---|
| `make run` | Run the display in the emulator at http://localhost:8888/ |
| `make debug` | Run the emulator with debug logging |
| `make test` | Run tests (pytest) |
| `make lint` | Lint check (ruff) |
| `make fixtures` | Save a live AirLabs response as a test fixture |
| `make deploy` | rsync the code to the Pi |
| `make setup-pi` | Install deps + build rpi-rgb-led-matrix (run on the Pi) |
| `make run-pi` | Run the app on the Pi (needs root for GPIO) |
| `make debug-pi` | Run on the Pi with debug logging |

## Configuration

Settings load from a YAML file pointed to by the `JETSET_CONFIG` environment
variable (defaults built in when unset). The `hardware` section tunes the
physical LED panel and is ignored by the emulator:

```yaml
hardware:
  panel_type: ""        # empty = no chip-specific init; set "FM6126A" only if the panel comes up garbled
  gpio_slowdown: 5      # raise if the image is unstable/corrupts; lower if the display lags
  multiplexing: 0       # 0 for standard 1/16-scan panels; nonzero only for outdoor/multiplexed
  row_address_type: 0   # 0 for standard panels; other values for some 1/16-scan panels (e.g. 3)
  rgb_sequence: RBG     # physical subpixel order; "RGB" for a standard panel, "RBG" for the current one
```

Flights come from a single source, **AirLabs** (`api_source: airlabs`): one
`/flights?bbox=` call returns every nearby flight with positions, metrics, and
route. `AIRLABS_API_KEY` is read from the environment or a `.env` file. The
free tier allows ~1000 requests/month, so the app refreshes every 45 minutes
(`refresh: 2700`) — one call per refresh — and the display slides a window
across all captured flights so fresh aircraft trickle in between refreshes.

## Data source history

How we got to a single AirLabs source (kept here so the decisions aren't relearned):

- **adsb.lol** (free) gave positions/metrics; **adsbdb** (free) gave routes by
  callsign; a **plausibility filter** (great-circle bearing + cross-track
  distance, in `geo.py`) tried to reject wrong routes; **hexdb.io** was a free
  cross-check.
- Measuring against **FlightAware AeroAPI** (authoritative, `scripts/route-compare.py`)
  showed adsbdb routes were only ~20% correct, and the plausibility filter had a
  great-circle bug (a route's *extended* great circle can pass near the receiver,
  so far-away routes slipped through). hexdb was sparse and years-stale.
- **AirLabs** matched AeroAPI in testing and returns positions, metrics, and
  route in one bbox call — so it replaced adsb.lol + adsbdb + hexdb + the
  plausibility filter. `AdsbLolAdapter` and `geo.py` remain only for the
  `route-compare` diagnostic and are slated for removal.
