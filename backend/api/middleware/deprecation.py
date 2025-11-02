from __future__ import annotations

from datetime import datetime
from typing import Callable

from fastapi import Request, Response


def deprecation_headers(*, sunset: str | None = None, link: str | None = None) -> Callable:
    """Return a simple middleware-like wrapper that adds deprecation headers.

    - Deprecation: true
    - Sunset: RFC 1123 datetime string (if provided)
    - Link: URL with rel="successor-version" (if provided)
    """

    def _apply_headers(request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        response: Response = call_next(request)  # type: ignore[misc]
        response.headers["Deprecation"] = "true"
        if sunset:
            response.headers["Sunset"] = sunset
        if link:
            response.headers["Link"] = f"<{link}>; rel=\"successor-version\""
        return response

    return _apply_headers


def rfc1123(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
