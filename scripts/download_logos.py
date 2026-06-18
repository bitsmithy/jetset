"""Download airline logos from the Jxck-S/airline-logos repository.

RadarBox is the preferred set; FlightAware fills the gaps RadarBox is missing
(e.g. ASA). Logos are cached in AppConfig.logo_dir as {ICAO}.png files; a file
already present (from a higher-priority source) is never overwritten.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast

from PIL import Image

from jetset.config import AppConfig

# (GitHub contents API, raw base) per source, in PRIORITY order — earlier
# sources win because the download skips files that already exist locally.
SOURCES = [
    (
        "https://api.github.com/repos/Jxck-S/airline-logos/contents/radarbox_logos",
        "https://raw.githubusercontent.com/Jxck-S/airline-logos/main/radarbox_logos",
    ),
    (
        "https://api.github.com/repos/Jxck-S/airline-logos/contents/flightaware_logos",
        "https://raw.githubusercontent.com/Jxck-S/airline-logos/main/flightaware_logos",
    ),
]


def _logo_dir() -> Path:
    """The configured logo cache directory."""
    return Path(AppConfig.load(os.environ.get("JETSET_CONFIG")).logo_dir)


def _fetch_logo_list(api_url: str) -> list[str]:
    """Fetch the list of PNG logo filenames from a GitHub contents API URL."""
    with urllib.request.urlopen(api_url) as resp:
        entries = json.loads(resp.read().decode())
    return [e["name"] for e in entries if e["name"].endswith(".png")]


def _is_blank_silhouette(path: Path) -> bool:
    """True if every opaque pixel is pure black — a silhouette the colour
    renderer skips entirely (it drops black pixels), so it shows as nothing.

    RadarBox ships a few such placeholders (e.g. ASA); treating them as gaps
    lets a later source (FlightAware) supply a real colour logo instead.
    """
    try:
        with Image.open(path) as img:
            rgba = img.convert("RGBA")
    except OSError:
        return False
    # PIL types pixels loosely; in RGBA mode each is an (r, g, b, a) tuple.
    pixels = cast("list[tuple[int, int, int, int]]", list(rgba.get_flattened_data()))
    return all(pixel[:3] == (0, 0, 0) for pixel in pixels if pixel[3] != 0)


def _download_missing(filenames: list[str], raw_base: str, dest_dir: Path) -> int:
    """Download each filename from raw_base into dest_dir.

    A file already present is kept — unless it's a blank silhouette, which this
    source is given the chance to replace with a usable colour logo.
    """
    count = 0
    for name in filenames:
        dest = dest_dir / name
        if dest.exists() and not _is_blank_silhouette(dest):
            continue
        try:
            urllib.request.urlretrieve(f"{raw_base}/{name}", dest)
            count += 1
        except (urllib.error.URLError, OSError):
            pass
    return count


def download_logos(icao_codes: list[str] | None = None) -> int:
    """Download airline logos to the configured logo dir, preferring earlier SOURCES.

    Args:
        icao_codes: Optional ICAO codes to fetch. If None, every logo each
            source offers is fetched — RadarBox first, then FlightAware for the
            codes RadarBox lacks.

    Returns:
        Number of logos newly downloaded.
    """
    dest_dir = _logo_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    explicit = [f"{code}.png" for code in icao_codes] if icao_codes is not None else None

    total = 0
    for api_url, raw_base in SOURCES:
        filenames = explicit if explicit is not None else _fetch_logo_list(api_url)
        total += _download_missing(filenames, raw_base, dest_dir)
    return total


if __name__ == "__main__":
    count = download_logos()
    print(f"Downloaded {count} airline logos to {_logo_dir()}")
