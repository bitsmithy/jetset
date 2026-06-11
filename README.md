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
