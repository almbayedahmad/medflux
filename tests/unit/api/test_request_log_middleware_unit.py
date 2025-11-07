from __future__ import annotations

import asyncio
import logging
from typing import Optional, Callable

import pytest
from fastapi import Response
from starlette.requests import Request

from backend.api.middleware.request_log import request_log_middleware


def _req(path: str = "/u", *, method: str = "GET", headers: Optional[dict[str, str]] = None, client: Optional[tuple[str, int]] = ("127.0.0.1", 12345)) -> Request:
    raw_headers = []
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode("latin1"), v.encode("latin1")))
    scope = {"type": "http", "http_version": "1.1", "method": method, "path": path, "headers": raw_headers}
    if client:
        scope["client"] = client
    return Request(scope)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_middleware_success_unit(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    req = _req(headers={"x-request-id": "RID-U1", "traceparent": "00-aaa-bbb-01", "user-agent": "pytest"})

    async def call_next(_: Request) -> Response:  # type: ignore[override]
        return Response(content=b"ok", status_code=200)

    resp = _run(request_log_middleware(req, call_next))
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == "RID-U1"
    assert resp.headers.get("traceparent") == "00-aaa-bbb-01"

    recs = [r for r in caplog.records if r.name == "medflux.api" and r.levelno == logging.INFO and r.getMessage() == "request"]
    assert recs, "no request info log emitted"
    rec = recs[-1]
    assert getattr(rec, "request_id", None) == "RID-U1"
    assert getattr(rec, "status", None) == 200
    assert isinstance(getattr(rec, "latency_ms", None), int)


def test_middleware_error_unit(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    req = _req(headers={"x-request-id": "RID-U2", "user-agent": "pytest"})

    async def call_next(_: Request) -> Response:  # type: ignore[override]
        raise RuntimeError("boom")

    resp = _run(request_log_middleware(req, call_next))
    assert resp.status_code == 500
    assert resp.headers.get("x-request-id") == "RID-U2"
    errs = [r for r in caplog.records if r.name == "medflux.api" and r.levelno >= logging.ERROR]
    assert errs, "no error log emitted"
    infos = [r for r in caplog.records if r.name == "medflux.api" and r.levelno == logging.INFO and r.getMessage() == "request"]
    assert infos, "no terminal request info log emitted"
