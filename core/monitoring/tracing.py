from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Dict, Iterator, Optional, Tuple

_READY = False
_TRACER = None

try:  # pragma: no cover
    from opentelemetry import trace as _trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ALWAYS_ON, ALWAYS_OFF
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _OTEL = True
except Exception:  # pragma: no cover
    _OTEL = False


def init_tracer() -> None:
    global _READY, _TRACER
    if _READY or not _OTEL:
        return
    try:
        # Honor explicit disable flags
        exporter_mode = str(os.environ.get("OTEL_TRACES_EXPORTER", "")).strip().lower()
        medflux_tracing = str(os.environ.get("MEDFLUX_TRACING", "")).strip().lower()
        # If explicitly disabled via MEDFLUX_TRACING, do not initialize
        if medflux_tracing and medflux_tracing not in {"1", "true", "yes"}:
            _READY = False
            return

        # Resource attributes: service, version, environment
        svc_name = os.environ.get("MEDFLUX_SERVICE_NAME") or os.environ.get("OTEL_SERVICE_NAME") or "medflux"
        svc_ver = os.environ.get("MEDFLUX_VERSION")
        env = os.environ.get("MEDFLUX_ENV") or os.environ.get("ENV")
        attrs = {"service.name": svc_name}
        if svc_ver:
            attrs["service.version"] = svc_ver
        if env:
            attrs["deployment.environment"] = env
        res = Resource.create(attrs)

        # Sampler from env MEDFLUX_TRACE_SAMPLING: 'always'/'never'/ratio 0..1
        sampler_cfg = (os.environ.get("MEDFLUX_TRACE_SAMPLING") or "").strip().lower()
        if sampler_cfg in {"always", "on", "1", "100%"}:
            sampler = ALWAYS_ON
        elif sampler_cfg in {"never", "off", "0", "0%"}:
            sampler = ALWAYS_OFF
        else:
            try:
                ratio = float(sampler_cfg)
                ratio = 0.0 if ratio < 0 else (1.0 if ratio > 1 else ratio)
                sampler = TraceIdRatioBased(ratio)
            except Exception:
                sampler = ALWAYS_ON

        provider = TracerProvider(resource=res, sampler=sampler)

        # Attach exporter only when not explicitly disabled
        if exporter_mode not in {"none", "off", "disabled", "0", "false", "no"} \
                and str(os.environ.get("MEDFLUX_TRACING_NOEXPORT", "")).strip().lower() not in {"1", "true", "yes"}:
            # Endpoint: use MEDFLUX_OTLP_ENDPOINT if set, else OTEL_* envs
            endpoint = os.environ.get("MEDFLUX_OTLP_ENDPOINT")
            exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
        _trace.set_tracer_provider(provider)
        _TRACER = _trace.get_tracer("medflux")
        _READY = True
    except Exception:
        _READY = False


def get_tracer():
    return _TRACER


@contextmanager
def span(name: str, attributes: Optional[Dict[str, object]] = None) -> Iterator[None]:
    if not _READY or _TRACER is None:
        yield
        return
    with _TRACER.start_as_current_span(name, attributes=attributes or {}):
        yield


def current_ids() -> Tuple[Optional[str], Optional[str]]:
    if not _READY:
        return None, None
    try:
        ctx = _trace.get_current_span().get_span_context()
        if not ctx or not ctx.is_valid:
            return None, None
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")
        return trace_id, span_id
    except Exception:
        return None, None
