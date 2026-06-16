"""Tests for the configuration loader."""

from pathlib import Path

import pytest
import yaml

from jetset.config import AppConfig


class TestConfigDefaults:
    def test_load_config_returns_frozen_dataclass(self) -> None:
        config = AppConfig.load()
        assert isinstance(config, AppConfig)
        with pytest.raises(AttributeError):
            config.home_lat = 0.0  # type: ignore[misc]

    def test_default_home_coordinates(self) -> None:
        config = AppConfig.load()
        assert isinstance(config.home_lat, float)
        assert isinstance(config.home_lon, float)
        assert -90 <= config.home_lat <= 90
        assert -180 <= config.home_lon <= 180

    def test_default_range(self) -> None:
        config = AppConfig.load()
        assert config.range > 0

    def test_default_pause(self) -> None:
        config = AppConfig.load()
        assert config.pause > 0

    def test_default_refresh(self) -> None:
        config = AppConfig.load()
        assert config.refresh > 0

    def test_default_panel_type_is_empty(self) -> None:
        # Empty = the library's default (no chip-specific init sequence). The
        # P2.5 64x32 panel renders correctly without one; see panel-diag sweep.
        config = AppConfig.load()
        assert config.hardware_panel_type == ""

    def test_default_gpio_slowdown(self) -> None:
        # Pi 3 A+ / Adafruit HAT needs 5 for a stable signal; 4 corrupted output.
        config = AppConfig.load()
        assert config.hardware_gpio_slowdown == 5

    def test_default_rgb_sequence(self) -> None:
        # The panel currently deployed needs "RBG"; standard panels use "RGB".
        config = AppConfig.load()
        assert config.hardware_rgb_sequence == "RBG"

    def test_default_multiplexing(self) -> None:
        config = AppConfig.load()
        assert config.hardware_multiplexing == 0

    def test_default_row_address_type(self) -> None:
        # Standard 1/16-scan addressing; 1 collapsed the image to two lines.
        config = AppConfig.load()
        assert config.hardware_row_address_type == 0


class TestConfigFromYaml:
    def test_loads_custom_yaml(self, tmp_path: Path) -> None:
        yaml_content = {
            "home": {"lat": 37.62, "lon": -122.38},
            "range": 80,
            "pause": 4,
            "refresh": 15,
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_content, f)

        config = AppConfig.load(str(config_path))
        assert config.home_lat == 37.62
        assert config.home_lon == -122.38
        assert config.range == 80
        assert config.pause == 4
        assert config.refresh == 15

    def test_loads_custom_hardware_section(self, tmp_path: Path) -> None:
        yaml_content = {
            "hardware": {"panel_type": "FM6127", "gpio_slowdown": 2, "rgb_sequence": "RGB"}
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_content, f)

        config = AppConfig.load(str(config_path))
        assert config.hardware_panel_type == "FM6127"
        assert config.hardware_gpio_slowdown == 2
        assert config.hardware_rgb_sequence == "RGB"

    def test_api_source_defaults_to_airlabs(self) -> None:
        config = AppConfig.load()
        assert config.api_source == "airlabs"
