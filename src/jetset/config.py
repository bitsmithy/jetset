from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class AppConfig:
    # IAH
    home_lat: float = 29.9931
    home_lon: float = -95.3416
    range: int = 200
    pause: int = 2
    refresh: int = 2700  # 45 min — one AirLabs bbox call per refresh ≈ 960/month
    api_source: str = "airlabs"
    # Physical LED panel tuning (ignored by the emulator). panel_type is empty
    # by default — the P2.5 64x32 panel needs no chip-specific init sequence.
    # Set it (e.g. "FM6126A") only if a panel comes up garbled without one.
    hardware_panel_type: str = ""
    # Pi 3 A+ / Adafruit HAT needs slowdown 5 for a stable signal; 4 produced
    # intermittent corruption that looked like scrambled pixels.
    hardware_gpio_slowdown: int = 5
    # Standard 1/16-scan panels use multiplexing 0 / row_address_type 0.
    # Override only for "outdoor"/multiplexed panels.
    hardware_multiplexing: int = 0
    hardware_row_address_type: int = 0
    # Physical subpixel order; "RGB" for a standard panel (verified with
    # scripts/panel-colors.py — solid red/green/blue all render true).
    hardware_rgb_sequence: str = "RGB"

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
