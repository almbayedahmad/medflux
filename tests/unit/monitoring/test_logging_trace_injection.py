from __future__ import annotations

import logging
import importlib
import os

import pytest


class CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        self.records.append(record)


def test_contextfilter_injects_trace_ids(monkeypatch):
    # Requires OTEL to be installed
    try:
        __import__("opentelemetry")
        __import__("opentelemetry.sdk")
        __import__("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    except Exception:
        pytest.skip("opentelemetry not installed")

    # Enable monitoring for tracer init and allow tracer exporter
    monkeypatch.setenv("MEDFLUX_MONITORING", "1")
    # Create tracer provider without exporting to avoid network calls
    monkeypatch.setenv("MEDFLUX_TRACING_NOEXPORT", "1")

    # Fresh modules
    for mod in [
        "core.monitoring.tracing",
        "core.monitoring",
    ]:
        if mod in list(importlib.sys.modules.keys()):
            importlib.reload(importlib.import_module(mod))

    from core.monitoring import init_monitoring
    from core.monitoring.tracing import span
    from core.logging.context import ContextFilter

    init_monitoring()

    logger = logging.getLogger("medflux.test")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    ch = CaptureHandler()
    ch.setLevel(logging.INFO)
    ch.addFilter(ContextFilter())
    logger.handlers[:] = [ch]

    with span("test-span", attributes={"k": "v"}):
        logger.info("hello")

    assert ch.records, "no log records captured"
    rec = ch.records[-1]
    # ContextFilter should inject trace_id/span_id on the record
    assert getattr(rec, "trace_id", None), "trace_id not injected"
