from __future__ import annotations

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


def _has_line(body: str, metric: str, labels: tuple[str, ...]) -> bool:
    for line in body.splitlines():
        if not line.startswith(metric + "{"):
            continue
        if all(lbl in line for lbl in labels):
            return True
    return False


def test_monitor_facade_inc_and_timer(monkeypatch):
    try:
        __import__("prometheus_client")
    except Exception:
        pytest.skip("prometheus_client not installed")

    from core.monitoring import get_monitor, init_monitoring

    port = _find_free_port()
    monkeypatch.setenv("MEDFLUX_MONITORING", "1")
    monkeypatch.setenv("MEDFLUX_PROM_PORT", str(port))

    init_monitoring()
    mon = get_monitor()
    flow = f"pytest_flow_{random.randint(1, 1_000_000)}"
    mon.inc("flow_runs_total", labels={"flow": flow})
    with mon.timer("flow_duration_ms", labels={"flow": flow}):
        time.sleep(0.05)

    time.sleep(0.2)
    status, body = _http_get(f"http://127.0.0.1:{port}/metrics")
    assert status == 200
    assert _has_line(body, "medflux_flow_runs_total", (f'flow="{flow}"',))
    assert _has_line(body, "medflux_flow_duration_ms_count", (f'flow="{flow}"',))
