#!/usr/bin/env -S uv run
"""Save live API responses as test fixtures.

Run all fixtures:
    make fixtures

Run a specific fixture:
    python scripts/save_fixtures.py adsblol
"""

import json
import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

from jetset.config import AppConfig
from jetset.fetcher import AirLabsAdapter

FIXTURES_DIR = "tests/fixtures"


@dataclass(frozen=True)
class FixtureProvider:
    adapter_class: type

    @property
    def name(self) -> str:
        cls_name = self.adapter_class.__name__
        suffix = "Adapter"
        if cls_name.endswith(suffix):
            cls_name = cls_name[: -len(suffix)]
        return cls_name.lower()

    @property
    def env_key(self) -> str:
        return f"{self.name.upper()}_API_KEY"

    @property
    def path(self) -> str:
        return f"{FIXTURES_DIR}/{self.name}_response.json"

    def save(self, config: AppConfig) -> None:
        api_key = os.environ.get(self.env_key)
        if api_key:
            adapter = self.adapter_class(api_key)
        else:
            try:
                adapter = self.adapter_class()
            except TypeError:
                print(f"Skipping {self.name}: {self.env_key} not set")
                return

        data = adapter.nearby_flights(config.home_lat, config.home_lon, config.range, raw=True)

        flights = data.get("flights", data) if isinstance(data, dict) else data
        os.makedirs(FIXTURES_DIR, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

        count = len(flights) if isinstance(flights, list) else 1
        print(f"Saved {count} {self.name} flight(s) to {self.path}")


FIXTURES: list[type] = [
    AirLabsAdapter,
]


def main() -> None:
    config = AppConfig.load()
    providers = [FixtureProvider(cls) for cls in FIXTURES]
    names = set(sys.argv[1:]) if len(sys.argv) > 1 else {p.name for p in providers}

    for p in providers:
        if p.name in names:
            p.save(config)

    requested = {*sys.argv[1:]}
    available = {p.name for p in providers}
    unknown = requested - available
    if unknown:
        list_available = ", ".join(sorted(available))
        print(
            f"Unknown fixture(s): {', '.join(sorted(unknown))}. Available: {list_available}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
