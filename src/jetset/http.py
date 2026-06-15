"""HTTP utilities for API communication."""

from typing import ClassVar

import requests


class RequestsAPI(requests.Session):
    """A requests.Session subclass that prepends a base URL to every request.

    Useful for API clients that talk to a single host — provides
    convenience like `api.get(\"/endpoint\")` without repeating
    the scheme and hostname.
    """

    base_url: ClassVar[str | None] = None

    def __init__(
        self, base_url: str | None = None, headers: dict[str, str] | None = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

        if headers:
            self.headers.update(headers)

    def request(self, method, url, *args, **kwargs):
        if self.base_url:
            url = self.base_url.rstrip("/") + url

        return super().request(method, url, *args, **kwargs)
