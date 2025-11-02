from __future__ import annotations

import logging
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.main import create_app


@pytest.fixture()
def app() -> FastAPI:
    a = create_app()

    @a.get("/boom")
    def boom() -> dict:  # type: ignore[override]
        raise RuntimeError("boom")

    return a


@pytest.mark.integration
def test_request_log_success(app: FastAPI, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    client = TestClient(app)
    r = client.get("/api/v1/health", headers={"x-request-id": "RID-123", "user-agent": "pytest"})
    assert r.status_code == 200
    # find the request log record
    recs = [
        rec for rec in caplog.records
        if rec.name == "medflux.api" and rec.levelno == logging.INFO and rec.getMessage() == "request"
    ]
    assert recs, "no request info log emitted"
    rec = recs[-1]
    assert getattr(rec, "method", None) == "GET"
    assert getattr(rec, "route", None) == "/api/v1/health"
    assert getattr(rec, "status", None) == 200
    assert getattr(rec, "request_id", None) == "RID-123"


@pytest.mark.integration
def test_request_log_error_path(app: FastAPI, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    client = TestClient(app)
    r = client.get("/boom", headers={"x-request-id": "RID-ERR", "user-agent": "pytest"})
    # middleware returns 500 with JSON body and echoes request id header
    assert r.status_code == 500
    hdr: Optional[str] = r.headers.get("x-request-id")
    assert hdr == "RID-ERR"
    # error record present
    err = [rec for rec in caplog.records if rec.name == "medflux.api" and rec.levelno >= logging.ERROR]
    assert err, "no error log emitted"
    # terminal info record present
    info = [rec for rec in caplog.records if rec.name == "medflux.api" and rec.levelno == logging.INFO and rec.getMessage() == "request"]
    assert info, "no terminal request info log emitted"


@pytest.mark.integration
def test_request_log_with_traceparent(app: FastAPI, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    client = TestClient(app)
    tp = "00-abcdef1234567890abcdef1234567890-1234567890abcdef-01"
    r = client.get("/api/v1/version", headers={"x-request-id": "RID-TP", "traceparent": tp, "user-agent": "pytest"})
    assert r.status_code == 200
    # Middleware should echo traceparent
    assert r.headers.get("traceparent") == tp
    # Find request info log and assert traceparent and latency present
    recs = [
        rec for rec in caplog.records
        if rec.name == "medflux.api" and rec.levelno == logging.INFO and rec.getMessage() == "request"
    ]
    assert recs, "no request info log emitted"
    rec = recs[-1]
    assert getattr(rec, "traceparent", None) == tp
    assert isinstance(getattr(rec, "latency_ms", None), int)
