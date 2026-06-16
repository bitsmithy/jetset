"""HTTP utilities for API communication."""

import os
from pathlib import Path
from typing import ClassVar

import requests

# Common locations for the system CA bundle on Linux
_SYSTEM_CA_BUNDLES = [
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/ca-bundle.pem",
]


def _find_ca_bundle() -> str | None:
    """Return a path to a valid CA bundle, or None."""
    # Honour an explicit env var first
    env = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if env and Path(env).is_file():
        return env
    for path in _SYSTEM_CA_BUNDLES:
        if Path(path).is_file():
            return path
    return None


class RequestsAPI(requests.Session):
    """A requests.Session subclass that prepends a base URL to every request.

    Useful for API clients that talk to a single host — provides
    convenience like `api.get("/endpoint")` without repeating
    the scheme and hostname.
    """

    base_url: ClassVar[str | None] = None

    def __init__(
        self, base_url: str | None = None, headers: dict[str, str] | None = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        # Use a detected system CA bundle if available, otherwise certifi
        ca_bundle = _find_ca_bundle()
        if ca_bundle:
            self.verify = ca_bundle
        self.base_url = base_url

        if headers:
            self.headers.update(headers)

    def request(self, method, url, *args, **kwargs):
        if self.base_url:
            url = self.base_url.rstrip("/") + url

        return super().request(method, url, *args, **kwargs)
