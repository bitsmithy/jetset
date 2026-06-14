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

    def test_default_cycle(self) -> None:
        config = AppConfig.load()
        assert config.cycle > 0

    def test_default_refresh(self) -> None:
        config = AppConfig.load()
        assert config.refresh > 0


class TestConfigFromYaml:
    def test_loads_custom_yaml(self, tmp_path: Path) -> None:
        yaml_content = {
            "home": {"lat": 37.62, "lon": -122.38},
            "range": 80,
            "cycle": 4,
            "refresh": 15,
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(yaml_content, f)

        config = AppConfig.load(str(config_path))
        assert config.home_lat == 37.62
        assert config.home_lon == -122.38
        assert config.range == 80
        assert config.cycle == 4
        assert config.refresh == 15

    def test_api_source_defaults_to_adsblol(self) -> None:
        config = AppConfig.load()
        assert config.api_source == "adsblol"
