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
| `make run` | Run the display emulator at http://localhost:8888/ |
| `make test` | Run tests (pytest) |
| `make lint` | Lint check (ruff) |

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
