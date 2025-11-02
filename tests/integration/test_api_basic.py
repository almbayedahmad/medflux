from __future__ import annotations

from typing import Optional

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from core.versioning import get_version_info


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert isinstance(data.get("version"), str)


@pytest.mark.integration
def test_version_endpoint(client: TestClient) -> None:
    r = client.get("/api/v1/version")
    assert r.status_code == 200
    data = r.json()
    app_info = data.get("app") or {}
    cur = get_version_info()
    assert app_info.get("version") == cur.get("version")
    schemas = data.get("schemas") or {}
    assert "stage_contract" in schemas


@pytest.mark.integration
def test_metrics_optional(client: TestClient) -> None:
    # /metrics exists only if prometheus_client is importable; both 200/404 are acceptable
    r = client.get("/metrics")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        ctype: Optional[str] = r.headers.get("content-type")
        assert ctype is None or "text/plain" in ctype
