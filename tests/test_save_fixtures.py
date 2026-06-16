"""Tests for the fixture saving utility."""

from unittest.mock import patch

from jetset.config import AppConfig
from scripts.save_fixtures import FixtureProvider


class TestFixtureProviderSave:
    def test_saves_keyless_adapter_without_api_key(self, tmp_path) -> None:
        from jetset.fetcher import AirLabsAdapter

        mock_data = [{"flight": "UAL1170 "}]

        with patch("scripts.save_fixtures.os.environ.get", return_value=None), \
                patch.object(AirLabsAdapter, "nearby_flights", return_value=mock_data):
            with patch("scripts.save_fixtures.FIXTURES_DIR", str(tmp_path)):
                provider = FixtureProvider(AirLabsAdapter)
                provider.save(AppConfig())

        expected_file = tmp_path / "airlabs_response.json"
        assert expected_file.exists()
