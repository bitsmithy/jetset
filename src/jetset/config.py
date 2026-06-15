from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class AppConfig:
    # IAH
    home_lat: float = 29.9931
    home_lon: float = -95.3416
    range: int = 200
    pause: int = 2
    refresh: int = 60
    api_source: str = "adsblol"

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
