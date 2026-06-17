"""Download airline logos from the Jxck-S/airline-logos repository.

RadarBox is the preferred set; FlightAware fills the gaps RadarBox is missing
(e.g. ASA). Logos are cached in ~/.cache/jetset/logos/ as {ICAO}.png files; a
file already present (from a higher-priority source) is never overwritten.
"""

import json
import urllib.error
import urllib.request

from jetset.display import LOGO_DIR

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


def _fetch_logo_list(api_url: str) -> list[str]:
    """Fetch the list of PNG logo filenames from a GitHub contents API URL."""
    with urllib.request.urlopen(api_url) as resp:
        entries = json.loads(resp.read().decode())
    return [e["name"] for e in entries if e["name"].endswith(".png")]


def _download_missing(filenames: list[str], raw_base: str) -> int:
    """Download each filename from raw_base into LOGO_DIR, skipping existing."""
    count = 0
    for name in filenames:
        dest = LOGO_DIR / name
        if dest.exists():
            continue
        try:
            urllib.request.urlretrieve(f"{raw_base}/{name}", dest)
            count += 1
        except (urllib.error.URLError, OSError):
            pass
    return count


def download_logos(icao_codes: list[str] | None = None) -> int:
    """Download airline logos to LOGO_DIR, preferring earlier SOURCES.

    Args:
        icao_codes: Optional ICAO codes to fetch. If None, every logo each
            source offers is fetched — RadarBox first, then FlightAware for the
            codes RadarBox lacks.

    Returns:
        Number of logos newly downloaded.
    """
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    explicit = [f"{code}.png" for code in icao_codes] if icao_codes is not None else None

    total = 0
    for api_url, raw_base in SOURCES:
        filenames = explicit if explicit is not None else _fetch_logo_list(api_url)
        total += _download_missing(filenames, raw_base)
    return total


if __name__ == "__main__":
    count = download_logos()
    print(f"Downloaded {count} airline logos to {LOGO_DIR}")
