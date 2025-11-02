from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional, Dict, Any
import time

from core.logging.context import set_ctx

_INIT_DONE = False


def init_monitoring() -> None:
    """Initialize metrics/tracing backends if enabled via env.

    Env:
    - MEDFLUX_MONITORING=1 to enable initialization (no-op otherwise)
    - MEDFLUX_PROM_PORT: start Prometheus HTTP exporter on this port (dev)
    - Standard OTEL_* envs for OpenTelemetry OTLP exporters
    """
    global _INIT_DONE
    if _INIT_DONE:
        return
    if str(os.environ.get("MEDFLUX_MONITORING", "")).strip().lower() not in {"1", "true", "yes"}:
        return
    try:
        from .metrics import init_metrics

        init_metrics()
    except Exception:
        pass
    try:
        from .tracing import init_tracer

        init_tracer()
    except Exception:
        pass
    _INIT_DONE = True


@contextmanager
def start_phase_span(phase: str, run_id: Optional[str] = None) -> Iterator[None]:
    """Open a tracing span for a phase and inject trace ids into log context."""
    try:
        from .tracing import span, current_ids

        with span("phase.run", attributes={"phase": phase, "run_id": run_id}):
            try:
                trace_id, span_id = current_ids()
                if trace_id:
                    set_ctx(trace_id=trace_id, span_id=span_id)
            except Exception:
                pass
            yield
    except Exception:
        # Tracing not available; still yield
        yield


def record_phase_run(phase: str, status: str) -> None:
    """Increment a phase run status counter if metrics are available."""
    try:
        from .metrics import record_phase_run

        record_phase_run(phase, status)
    except Exception:
        pass


# Re-export commonly used metric function for convenience
try:  # pragma: no cover - import-time guard
    from .metrics import record_validation as record_validation  # type: ignore
except Exception:  # pragma: no cover
    pass


@contextmanager
def validation_span(kind: str, phase: str) -> Iterator[Dict[str, Any]]:
    """Context that opens a validation span and records metrics on exit.

    Usage:
        with validation_span("input", phase) as v:
            # set v["ok"] = True/False and optional v["code"]
            ...
    """
    t0 = time.perf_counter()
    state: Dict[str, Any] = {"ok": True, "code": None}
    try:
        from .tracing import span as _span
    except Exception:
        _span = None

    if _span is None:
        try:
            yield state
        finally:
            try:
                from .metrics import record_validation as _rec

                _rec(kind, phase, bool(state.get("ok", True)), state.get("code"), (time.perf_counter() - t0) * 1000.0)
            except Exception:
                pass
        return

    with _span(f"validation.{kind}", attributes={"phase": phase}):
        try:
            yield state
        finally:
            try:
                from .metrics import record_validation as _rec

                _rec(kind, phase, bool(state.get("ok", True)), state.get("code"), (time.perf_counter() - t0) * 1000.0)
            except Exception:
                pass


class _Timer:
    def __init__(self, cb):
        self._cb = cb
        self._t0 = 0.0

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        dt_ms = (time.perf_counter() - self._t0) * 1000.0
        try:
            self._cb(dt_ms)
        except Exception:
            pass
        return False


class Monitor:
    """Lightweight facade for common app-level metrics.

    Supports:
    - inc("flow_runs_total", labels={"flow": name})
    - timer("flow_duration_ms", labels={"flow": name})
    """

    def inc(self, metric: str, *, labels: Optional[Dict[str, str]] = None) -> None:
        labels = labels or {}
        if metric == "flow_runs_total" and "flow" in labels:
            try:
                from .metrics import record_flow_run

                record_flow_run(labels["flow"])  # type: ignore[arg-type]
            except Exception:
                pass

    def timer(self, metric: str, *, labels: Optional[Dict[str, str]] = None) -> _Timer:
        labels = labels or {}
        if metric == "flow_duration_ms" and "flow" in labels:
            try:
                from .metrics import observe_flow_duration

                return _Timer(lambda ms: observe_flow_duration(labels["flow"], ms))  # type: ignore[arg-type]
            except Exception:
                return _Timer(lambda ms: None)
        return _Timer(lambda ms: None)


def get_monitor(**_kwargs: Any) -> Monitor:
    """Return a monitor facade instance.

    Arguments are accepted for future use (logger/version/etc.).
    """
    return Monitor()


# Convenience re-exports for added app metrics
try:  # pragma: no cover
    from .metrics import (
        record_doc_processed as record_doc_processed,  # type: ignore
        observe_ocr_time_ms as observe_ocr_time_ms,  # type: ignore
        observe_ocr_confidence as observe_ocr_confidence,  # type: ignore
        observe_api_request as observe_api_request,  # type: ignore
        observe_phase_step_duration as observe_phase_step_duration,  # type: ignore
        observe_io_duration as observe_io_duration,  # type: ignore
        record_io_error as record_io_error,  # type: ignore
        record_validator_request as record_validator_request,  # type: ignore
        record_validator_compile as record_validator_compile,  # type: ignore
    )
except Exception:
    pass
