from __future__ import annotations

from typing import Optional

from fastapi import Response
from starlette.requests import Request

from backend.api.middleware.request_log import extract_request_meta, enrich_response_headers


def _build_request(method: str = "GET", path: str = "/x", headers: Optional[dict[str, str]] = None, client: Optional[tuple[str, int]] = ("127.0.0.1", 12345)) -> Request:
    raw_headers = []
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode("latin1"), v.encode("latin1")))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "headers": raw_headers,
    }
    if client:
        scope["client"] = client
    return Request(scope)


def test_extract_request_meta_defaults():
    req = _build_request()
    meta = extract_request_meta(req)
    assert meta["method"] == "GET"
    assert meta["path"] == "/x"
    # No route object, so route == path
    assert meta["route"] == "/x"
    assert meta["client"] == "127.0.0.1"
    assert meta["user_agent"] is None
    assert meta["traceparent"] is None
    assert isinstance(meta["request_id"], str) and meta["request_id"]


def test_extract_request_meta_headers():
    req = _build_request(
        method="POST",
        path="/y",
        headers={"user-agent": "pytest", "x-request-id": "RID-1", "traceparent": "00-aaaa-bbbb-01"},
    )
    meta = extract_request_meta(req)
    assert meta["method"] == "POST"
    assert meta["user_agent"] == "pytest"
    assert meta["request_id"] == "RID-1"
    assert meta["traceparent"] == "00-aaaa-bbbb-01"


def test_enrich_response_headers():
    r = Response()
    enrich_response_headers(r, request_id="RID-2", traceparent="tp")
    assert r.headers.get("x-request-id") == "RID-2"
    assert r.headers.get("traceparent") == "tp"

