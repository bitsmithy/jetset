"""Tests for the airline logo downloader."""

from pathlib import Path

from PIL import Image

BLACK_OPAQUE = (0, 0, 0, 255)
TEAL_OPAQUE = (11, 67, 104, 255)


def _save_solid(path: Path, color: tuple[int, int, int, int]) -> None:
    """Write a tiny solid-colour RGBA PNG."""
    Image.new("RGBA", (4, 4), color).save(path)


class TestIsBlankSilhouette:
    def test_true_when_every_opaque_pixel_is_black(self, tmp_path: Path) -> None:
        from scripts.download_logos import _is_blank_silhouette

        path = tmp_path / "ASA.png"
        _save_solid(path, BLACK_OPAQUE)
        assert _is_blank_silhouette(path) is True

    def test_false_when_an_opaque_pixel_is_coloured(self, tmp_path: Path) -> None:
        from scripts.download_logos import _is_blank_silhouette

        path = tmp_path / "UAL.png"
        _save_solid(path, TEAL_OPAQUE)
        assert _is_blank_silhouette(path) is False


class TestDownloadMissing:
    def _coloured_downloader(self):
        """A urlretrieve stand-in that always writes a coloured logo."""

        def fake(_url: str, dest: Path) -> None:
            _save_solid(Path(dest), TEAL_OPAQUE)

        return fake

    def test_keeps_an_existing_coloured_logo(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        from scripts.download_logos import _download_missing

        _save_solid(tmp_path / "UAL.png", TEAL_OPAQUE)
        with patch("scripts.download_logos.urllib.request.urlretrieve") as mock_get:
            _download_missing(["UAL.png"], "https://raw/base", tmp_path)

        mock_get.assert_not_called()

    def test_replaces_an_existing_black_silhouette(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        from scripts.download_logos import _download_missing

        _save_solid(tmp_path / "ASA.png", BLACK_OPAQUE)
        with patch(
            "scripts.download_logos.urllib.request.urlretrieve",
            side_effect=self._coloured_downloader(),
        ) as mock_get:
            _download_missing(["ASA.png"], "https://raw/base", tmp_path)

        mock_get.assert_called_once()
