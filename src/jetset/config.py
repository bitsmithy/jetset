from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class AppConfig:
    # HEB
    home_lat: float = 30.0689232902742
    home_lon: float = -95.25178382821562
    range: int = 100  # in km
    pause: int = 5  # how long in seconds to wait between cycling through the pages of a flight
    cycles_per_flight: int = 2  # how many times to show all details per flight
    refresh: int = 2700  # 45 min — one AirLabs bbox call per refresh ≈ 960/month
    api_source: str = "airlabs"
    # Where airline logos are cached. A global path (not a user home) so the
    # root service and the deploy-user downloader resolve the same directory.
    logo_dir: str = "/var/lib/jetset/logos"

    @classmethod
    def load(cls, path=None):
        if path:
            with open(path, "r") as file:
                data = yaml.safe_load(file)
                if data:
                    flattened_data = {}
                    for k, v in data.items():
                        if isinstance(v, dict):
                            for x, y in v.items():
                                flattened_data[f"{k}_{x}"] = y
                        else:
                            flattened_data[k] = v

                    class_attrs = cls.__dataclass_fields__
                    attrs = {k: v for k, v in flattened_data.items() if k in class_attrs}
                    return cls(**attrs)

        return cls()
