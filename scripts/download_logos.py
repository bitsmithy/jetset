"""Download airline logos from the Jxck-S/airline-logos repository (RadarBox set).

Logos are cached locally in ~/.cache/jetset/logos/ as {ICAO}.png files.
"""

import json
import urllib.error
import urllib.request

from jetset.display import LOGO_DIR

REPO_API = "https://api.github.com/repos/Jxck-S/airline-logos/contents/radarbox_logos"
RAW_BASE = "https://raw.githubusercontent.com/Jxck-S/airline-logos/main/radarbox_logos"


def _fetch_logo_list() -> list[str]:
    """Fetch the list of logo filenames from the GitHub API."""
    with urllib.request.urlopen(REPO_API) as resp:
        entries = json.loads(resp.read().decode())
    return [e["name"] for e in entries if e["name"].endswith(".png")]


def download_logos(icao_codes: list[str] | None = None) -> int:
    """Download airline logos to LOGO_DIR.

    Args:
        icao_codes: Optional list of ICAO codes to download. If None, every
            logo in the repo is downloaded.

    Returns:
        Number of logos downloaded.
    """
    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    if icao_codes is not None:
        filenames = [f"{code}.png" for code in icao_codes]
    else:
        filenames = _fetch_logo_list()

    count = 0
    for name in filenames:
        dest = LOGO_DIR / name
        if dest.exists():
            continue
        url = f"{RAW_BASE}/{name}"
        try:
            urllib.request.urlretrieve(url, dest)
            count += 1
        except (urllib.error.URLError, OSError):
            pass

    return count


if __name__ == "__main__":
    count = download_logos()
    print(f"Downloaded {count} airline logos to {LOGO_DIR}")
