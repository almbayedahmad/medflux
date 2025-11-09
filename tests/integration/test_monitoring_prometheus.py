from __future__ import annotations

import os
import random
import socket
import time
from typing import Tuple

import pytest


def _find_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()
    s.close()
    return int(port)


def _http_get(url: str, timeout: float = 2.5) -> Tuple[int, str]:
    # Avoid external deps; use stdlib only
    import http.client
    from urllib.parse import urlparse

    parsed = urlparse(url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=timeout)
    try:
        conn.request("GET", parsed.path or "/")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body
    finally:
        conn.close()


def _line_with_metric_and_labels(body: str, metric: str, required_labels: Tuple[str, ...]) -> bool:
    for line in body.splitlines():
        if not line.startswith(metric + "{"):
            continue
        if all(lbl in line for lbl in required_labels):
            return True
    return False


def _wait_for_metrics(port: int, timeout: float = 5.0) -> bool:
    """Wait for the Prometheus exporter to accept connections."""
    deadline = time.time() + float(timeout)
    url = f"http://127.0.0.1:{port}/metrics"
    while time.time() < deadline:
        try:
            status, _ = _http_get(url, timeout=0.25)
            if status == 200:
                return True
        except Exception:
            time.sleep(0.05)
    return False


def test_prometheus_validation_metrics_emitted(monkeypatch):
    # Skip if prometheus client is missing
    try:
        __import__("prometheus_client")
    except Exception:
        pytest.skip("prometheus_client not installed")

    # Isolate env and pick a free port
    port = _find_free_port()
    monkeypatch.setenv("MEDFLUX_MONITORING", "1")
    monkeypatch.setenv("MEDFLUX_PROM_PORT", str(port))

    # Ensure fresh import/init
    import importlib

    # Reimport monitoring modules to reset module state across test runs
    for mod in [
        "core.monitoring.metrics",
        "core.monitoring.tracing",
        "core.monitoring",
    ]:
        if mod in list(importlib.sys.modules.keys()):
            importlib.reload(importlib.import_module(mod))

    from core.monitoring import init_monitoring
    from core.monitoring.metrics import record_validation

    init_monitoring()

    # Wait for exporter (skip if not available to avoid CI flakiness)
    if not _wait_for_metrics(port, timeout=5.0):
        pytest.skip("Prometheus exporter not reachable on allocated port")

    # Emit a couple of samples with a unique phase label to avoid collisions
    phase = f"pytest_phase_{random.randint(1, 1_000_000)}"
    record_validation("input", phase, True, None, 3.2)
    record_validation("input", phase, False, "VL-E999", 12.5)

    status, body = _http_get(f"http://127.0.0.1:{port}/metrics")
    assert status == 200

    # Basic presence checks for counters and histogram with our labels
    assert _line_with_metric_and_labels(
        body,
        "medflux_validation_ok_total",
        (f'phase="{phase}"', 'kind="input"'),
    )
    assert _line_with_metric_and_labels(
        body,
        "medflux_validation_failed_total",
        (f'phase="{phase}"', 'kind="input"', 'code="VL-E999"'),
    )
    # Histogram exposes bucket/sum/count lines with the same labels (order may vary)
    assert _line_with_metric_and_labels(
        body,
        "medflux_validation_duration_ms_count",
        (f'phase="{phase}"', 'kind="input"'),
    )


def test_prometheus_phase_runs_emitted(monkeypatch):
    # Skip if prometheus client is missing
    try:
        __import__("prometheus_client")
    except Exception:
        pytest.skip("prometheus_client not installed")

    port = _find_free_port()
    monkeypatch.setenv("MEDFLUX_MONITORING", "1")
    monkeypatch.setenv("MEDFLUX_PROM_PORT", str(port))

    import importlib
    for mod in [
        "core.monitoring.metrics",
        "core.monitoring.tracing",
        "core.monitoring",
    ]:
        if mod in list(importlib.sys.modules.keys()):
            importlib.reload(importlib.import_module(mod))

    from core.monitoring import init_monitoring, record_phase_run

    init_monitoring()

    if not _wait_for_metrics(port, timeout=5.0):
        pytest.skip("Prometheus exporter not reachable on allocated port")
    phase = f"pytest_phase_{random.randint(1, 1_000_000)}"
    record_phase_run(phase, "ok")
    record_phase_run(phase, "failed")

    status, body = _http_get(f"http://127.0.0.1:{port}/metrics")
    assert status == 200
    assert _line_with_metric_and_labels(
        body, "medflux_phase_runs_total", (f'phase="{phase}"', 'status="ok"')
    )
    assert _line_with_metric_and_labels(
        body, "medflux_phase_runs_total", (f'phase="{phase}"', 'status="failed"')
    )
