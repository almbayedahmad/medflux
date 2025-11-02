from __future__ import annotations

import importlib
import random
import time

import pytest


def test_start_phase_span_context(monkeypatch):
    # Enable monitoring; tracing init depends on OTEL packages being installed
    monkeypatch.setenv("MEDFLUX_MONITORING", "1")
    # Create tracer provider without exporting to avoid network calls
    monkeypatch.setenv("MEDFLUX_TRACING_NOEXPORT", "1")

    # Reset modules to ensure a clean init path per test run
    for mod in [
        "core.monitoring.tracing",
        "core.monitoring.metrics",
        "core.monitoring",
    ]:
        if mod in list(importlib.sys.modules.keys()):
            importlib.reload(importlib.import_module(mod))

    from core.monitoring import init_monitoring, start_phase_span
    from core.logging.context import get_ctx

    # Detect whether OTEL is available in this environment
    otel_available = True
    try:
        __import__("opentelemetry")
        __import__("opentelemetry.sdk")
        __import__("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    except Exception:
        otel_available = False

    init_monitoring()

    phase = f"pytest_phase_{random.randint(1, 1_000_000)}"
    with start_phase_span(phase, run_id="run-ctx-check"):
        ctx = get_ctx()
        if otel_available:
            # When tracing is available and initialized, trace ids should be injected
            assert ctx.get("trace_id"), "trace_id should be present when OTEL is available"
            # span_id may be None early; presence is best-effort
        else:
            # Without OTEL, no trace ids should be set
            assert "trace_id" not in ctx
