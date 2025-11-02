from __future__ import annotations

import os
import threading
import time
from typing import Optional, Dict, Any
import socket

_PROM_READY = False
_OTEL_READY = False

_lock = threading.Lock()

# Prometheus backend (dev)
try:  # pragma: no cover
    from prometheus_client import Counter as _PCounter
    from prometheus_client import Histogram as _PHistogram
    from prometheus_client import start_http_server

    _prom_validation_ok = _PCounter(
        "medflux_validation_ok_total",
        "Validation OK total",
        labelnames=("phase", "kind"),
    )
    _prom_validation_failed = _PCounter(
        "medflux_validation_failed_total",
        "Validation failed total",
        labelnames=("phase", "kind", "code"),
    )
    _prom_validation_duration = _PHistogram(
        "medflux_validation_duration_ms",
        "Validation duration in milliseconds",
        labelnames=("phase", "kind"),
        buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000),
    )
    _prom_phase_runs = _PCounter(
        "medflux_phase_runs_total",
        "Phase runs total",
        labelnames=("phase", "status"),
    )
    _prom_flow_runs = _PCounter(
        "medflux_flow_runs_total",
        "Flow runs total",
        labelnames=("flow",),
    )
    _prom_flow_duration = _PHistogram(
        "medflux_flow_duration_ms",
        "Flow duration in milliseconds",
        labelnames=("flow",),
        buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000),
    )
    _PROM_IMPORTED = True
except Exception:  # pragma: no cover
    _PROM_IMPORTED = False


# OpenTelemetry Metrics backend (prod)
try:  # pragma: no cover
    from opentelemetry import metrics as _otel_metrics
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    _OTEL_IMPORTED = True
except Exception:  # pragma: no cover
    _OTEL_IMPORTED = False

_otel_meter = None
_otel_validation_ok = None
_otel_validation_failed = None
_otel_validation_duration = None
_otel_phase_runs = None
_otel_flow_runs = None
_otel_flow_duration = None
_prom_docs_processed = None
_prom_doc_bytes = None
_prom_ocr_time = None
_prom_ocr_confidence = None
_prom_api_requests = None
_prom_api_duration = None
_otel_docs_processed = None
_otel_doc_bytes = None
_otel_ocr_time = None
_otel_ocr_confidence = None
_otel_api_requests = None
_otel_api_duration = None
_prom_step_duration = None
_otel_step_duration = None
_prom_io_duration = None
_otel_io_duration = None
_prom_io_errors = None
_otel_io_errors = None
_prom_validator_requests = None
_prom_validator_compiles = None
_otel_validator_requests = None
_otel_validator_compiles = None


def _wait_http_server(port: int, *, timeout_s: float = 5.0) -> bool:
    """Wait briefly for the Prometheus HTTP server to accept connections.

    Polls 127.0.0.1:port until connected or timeout reached.
    """
    deadline = time.time() + float(timeout_s)
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.2):
                return True
        except Exception:
            time.sleep(0.05)
    return False


def init_metrics() -> None:
    global _PROM_READY, _OTEL_READY, _otel_meter
    # Prometheus
    if _PROM_IMPORTED and not _PROM_READY:
        port = os.environ.get("MEDFLUX_PROM_PORT")
        if port:
            # Try to bind to 127.0.0.1, then fall back to default addr
            for addr in ("127.0.0.1", None):
                try:
                    if addr is None:
                        start_http_server(int(port))
                    else:
                        start_http_server(int(port), addr=addr)
                    # Ensure the thread is ready to accept connections
                    if _wait_http_server(int(port)):
                        _PROM_READY = True
                        break
                except Exception:
                    continue
    # OpenTelemetry Metrics
    if _OTEL_IMPORTED and not _OTEL_READY:
        try:
            # Honor explicit disable flags
            exporter_mode = str(os.environ.get("OTEL_METRICS_EXPORTER", "")).strip().lower()
            medflux_metrics = str(os.environ.get("MEDFLUX_METRICS", "")).strip().lower()
            if medflux_metrics and medflux_metrics not in {"1", "true", "yes"}:
                return
            if exporter_mode in {"none", "off", "disabled", "0", "false", "no"} or \
               str(os.environ.get("MEDFLUX_METRICS_NOEXPORT", "")).strip().lower() in {"1", "true", "yes"}:
                # Do not initialize OTEL metrics exporter
                return

            exporter = OTLPMetricExporter()  # uses OTEL_EXPORTER_OTLP_* envs
            reader = PeriodicExportingMetricReader(exporter)
            provider = MeterProvider(metric_readers=[reader])
            _otel_metrics.set_meter_provider(provider)
            _otel_meter = _otel_metrics.get_meter("medflux")
            global _otel_validation_ok, _otel_validation_failed, _otel_validation_duration, _otel_phase_runs, _otel_flow_runs, _otel_flow_duration
            global _otel_docs_processed, _otel_doc_bytes, _otel_ocr_time, _otel_ocr_confidence, _otel_api_requests, _otel_api_duration
            _otel_validation_ok = _otel_meter.create_counter("medflux.validation.ok")
            _otel_validation_failed = _otel_meter.create_counter("medflux.validation.failed")
            _otel_validation_duration = _otel_meter.create_histogram("medflux.validation.duration.ms")
            _otel_phase_runs = _otel_meter.create_counter("medflux.phase.runs")
            _otel_flow_runs = _otel_meter.create_counter("medflux.flow.runs")
            _otel_flow_duration = _otel_meter.create_histogram("medflux.flow.duration.ms")
            _otel_docs_processed = _otel_meter.create_counter("medflux.docs.processed")
            _otel_doc_bytes = _otel_meter.create_histogram("medflux.doc.bytes")
            _otel_ocr_time = _otel_meter.create_histogram("medflux.ocr.time.ms")
            _otel_ocr_confidence = _otel_meter.create_histogram("medflux.ocr.confidence")
            _otel_api_requests = _otel_meter.create_counter("medflux.api.requests")
            _otel_api_duration = _otel_meter.create_histogram("medflux.api.duration.ms")
            _otel_step_duration = _otel_meter.create_histogram("medflux.phase.step.duration.ms")
            _otel_io_duration = _otel_meter.create_histogram("medflux.io.duration.ms")
            _otel_io_errors = _otel_meter.create_counter("medflux.io.errors")
            _otel_validator_requests = _otel_meter.create_counter("medflux.validator.requests")
            _otel_validator_compiles = _otel_meter.create_counter("medflux.validator.compiles")
            _OTEL_READY = True
        except Exception:
            pass


def _get_exemplar() -> Optional[Dict[str, Any]]:
    """Return exemplar labels with trace_id when tracing is active (Prometheus only)."""
    try:
        from .tracing import current_ids

        tid, _sid = current_ids()
        if tid:
            return {"trace_id": tid}
    except Exception:
        return None
    return None


def _prom_inc(counter, labels: Dict[str, Any]) -> None:
    try:
        ex = _get_exemplar()
        if ex is not None:
            counter.labels(**labels).inc(exemplar=ex)  # type: ignore[call-arg]
        else:
            counter.labels(**labels).inc()
    except TypeError:
        # inc(exemplar=...) not supported in this client version
        try:
            counter.labels(**labels).inc()
        except Exception:
            pass
    except Exception:
        pass


def _prom_obs(hist, labels: Optional[Dict[str, Any]], value: float) -> None:
    try:
        ex = _get_exemplar()
        if labels is not None:
            if ex is not None:
                hist.labels(**labels).observe(value, exemplar=ex)  # type: ignore[call-arg]
            else:
                hist.labels(**labels).observe(value)
        else:
            if ex is not None:
                hist.observe(value, exemplar=ex)  # type: ignore[call-arg]
            else:
                hist.observe(value)
    except TypeError:
        try:
            if labels is not None:
                hist.labels(**labels).observe(value)
            else:
                hist.observe(value)
        except Exception:
            pass
    except Exception:
        pass


def record_validation(kind: str, phase: str, ok: bool, code: Optional[str], duration_ms: float) -> None:
    # Prometheus
    if _PROM_READY:
        try:
            if ok:
                _prom_inc(_prom_validation_ok, {"phase": phase, "kind": kind})
            else:
                _prom_inc(_prom_validation_failed, {"phase": phase, "kind": kind, "code": code or ""})
            _prom_obs(_prom_validation_duration, {"phase": phase, "kind": kind}, float(duration_ms))
        except Exception:
            pass
    # OpenTelemetry
    if _OTEL_READY and _otel_meter is not None:
        try:
            attrs = {"phase": phase, "kind": kind}
            if ok:
                _otel_validation_ok.add(1, attributes=attrs)
            else:
                attrs_failed = dict(attrs)
                attrs_failed["code"] = code or ""
                _otel_validation_failed.add(1, attributes=attrs_failed)
            _otel_validation_duration.record(float(duration_ms), attributes=attrs)
        except Exception:
            pass


def record_phase_run(phase: str, status: str) -> None:
    if _PROM_READY:
        try:
            _prom_inc(_prom_phase_runs, {"phase": phase, "status": status})
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_phase_runs.add(1, attributes={"phase": phase, "status": status})
        except Exception:
            pass


def record_flow_run(flow: str) -> None:
    if _PROM_READY:
        try:
            _prom_inc(_prom_flow_runs, {"flow": flow})
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_flow_runs.add(1, attributes={"flow": flow})
        except Exception:
            pass


def observe_flow_duration(flow: str, duration_ms: float) -> None:
    if _PROM_READY:
        try:
            _prom_obs(_prom_flow_duration, {"flow": flow}, float(duration_ms))
        except Exception:
            pass


def record_doc_processed(phase: str, doc_type: str, *, bytes_count: Optional[int] = None) -> None:
    if _PROM_READY:
        global _prom_docs_processed, _prom_doc_bytes
        try:
            if _prom_docs_processed is None:
                _prom_docs_processed = _PCounter(
                    "medflux_docs_processed_total",
                    "Documents processed total",
                    labelnames=("phase", "type"),
                )
            _prom_inc(_prom_docs_processed, {"phase": phase, "type": doc_type})
            if bytes_count is not None:
                if _prom_doc_bytes is None:
                    _prom_doc_bytes = _PHistogram(
                        "medflux_doc_bytes",
                        "Document size in bytes",
                        labelnames=("phase",),
                        buckets=(1e3, 1e4, 1e5, 5e5, 1e6, 5e6, 1e7, 5e7, 1e8),
                    )
                _prom_obs(_prom_doc_bytes, {"phase": phase}, float(bytes_count))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_docs_processed.add(1, attributes={"phase": phase, "type": doc_type})
            if bytes_count is not None:
                _otel_doc_bytes.record(float(bytes_count), attributes={"phase": phase})
        except Exception:
            pass


def observe_ocr_time_ms(duration_ms: float) -> None:
    if _PROM_READY:
        global _prom_ocr_time
        try:
            if _prom_ocr_time is None:
                _prom_ocr_time = _PHistogram(
                    "medflux_ocr_time_ms",
                    "OCR time per page in milliseconds",
                    buckets=(10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000),
                )
            _prom_obs(_prom_ocr_time, None, float(duration_ms))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_ocr_time.record(float(duration_ms))
        except Exception:
            pass


def observe_ocr_confidence(conf: float) -> None:
    if conf is None:
        return
    if _PROM_READY:
        global _prom_ocr_confidence
        try:
            if _prom_ocr_confidence is None:
                _prom_ocr_confidence = _PHistogram(
                    "medflux_ocr_confidence",
                    "OCR average confidence (0..100)",
                    buckets=(10, 20, 30, 40, 50, 60, 70, 80, 90, 100),
                )
            _prom_obs(_prom_ocr_confidence, None, float(conf))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_ocr_confidence.record(float(conf))
        except Exception:
            pass


def observe_api_request(route: str, method: str, status: int, duration_ms: float) -> None:
    if _PROM_READY:
        global _prom_api_requests, _prom_api_duration
        try:
            if _prom_api_requests is None:
                _prom_api_requests = _PCounter(
                    "medflux_api_requests_total",
                    "API requests total",
                    labelnames=("route", "method", "status"),
                )
            if _prom_api_duration is None:
                _prom_api_duration = _PHistogram(
                    "medflux_api_duration_ms",
                    "API request duration in milliseconds",
                    labelnames=("route", "method", "status"),
                    buckets=(5, 10, 20, 50, 100, 200, 500, 1000, 2000),
                )
            status_s = str(status)
            _prom_inc(_prom_api_requests, {"route": route, "method": method, "status": status_s})
            _prom_obs(_prom_api_duration, {"route": route, "method": method, "status": status_s}, float(duration_ms))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            attrs = {"route": route, "method": method, "status": str(status)}
            _otel_api_requests.add(1, attributes=attrs)
            _otel_api_duration.record(float(duration_ms), attributes=attrs)
        except Exception:
            pass


def observe_phase_step_duration(phase: str, step: str, duration_ms: float) -> None:
    if _PROM_READY:
        global _prom_step_duration
        try:
            if _prom_step_duration is None:
                _prom_step_duration = _PHistogram(
                    "medflux_phase_step_duration_ms",
                    "Phase step duration in milliseconds",
                    labelnames=("phase", "step"),
                    buckets=(5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000),
                )
            _prom_obs(_prom_step_duration, {"phase": phase, "step": step}, float(duration_ms))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_step_duration.record(float(duration_ms), attributes={"phase": phase, "step": step})
        except Exception:
            pass


def observe_io_duration(op: str, kind: str, duration_ms: float) -> None:
    if _PROM_READY:
        global _prom_io_duration
        try:
            if _prom_io_duration is None:
                _prom_io_duration = _PHistogram(
                    "medflux_io_duration_ms",
                    "I/O operation duration in milliseconds",
                    labelnames=("op", "kind"),
                    buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000),
                )
            _prom_obs(_prom_io_duration, {"op": op, "kind": kind}, float(duration_ms))
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_io_duration.record(float(duration_ms), attributes={"op": op, "kind": kind})
        except Exception:
            pass


def record_io_error(op: str, kind: str) -> None:
    if _PROM_READY:
        global _prom_io_errors
        try:
            if _prom_io_errors is None:
                _prom_io_errors = _PCounter(
                    "medflux_io_errors_total",
                    "I/O error events",
                    labelnames=("op", "kind"),
                )
            _prom_inc(_prom_io_errors, {"op": op, "kind": kind})
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_io_errors.add(1, attributes={"op": op, "kind": kind})
        except Exception:
            pass


def record_validator_request(kind: str, phase: str) -> None:
    if _PROM_READY:
        global _prom_validator_requests
        try:
            if _prom_validator_requests is None:
                _prom_validator_requests = _PCounter(
                    "medflux_validator_requests_total",
                    "Validator request count",
                    labelnames=("phase", "kind"),
                )
            _prom_inc(_prom_validator_requests, {"phase": phase, "kind": kind})
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_validator_requests.add(1, attributes={"phase": phase, "kind": kind})
        except Exception:
            pass


def record_validator_compile(kind: str, phase: str) -> None:
    if _PROM_READY:
        global _prom_validator_compiles
        try:
            if _prom_validator_compiles is None:
                _prom_validator_compiles = _PCounter(
                    "medflux_validator_compiles_total",
                    "Validator compile count (cache miss)",
                    labelnames=("phase", "kind"),
                )
            _prom_inc(_prom_validator_compiles, {"phase": phase, "kind": kind})
        except Exception:
            pass
    if _OTEL_READY and _otel_meter is not None:
        try:
            _otel_validator_compiles.add(1, attributes={"phase": phase, "kind": kind})
        except Exception:
            pass
