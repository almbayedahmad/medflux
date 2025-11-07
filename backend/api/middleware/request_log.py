from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
import uuid
from core.logging import get_logger
from core.monitoring import observe_api_request
from core.monitoring.tracing import span


def extract_request_meta(request: Request) -> dict:
    """Extract request metadata for logging and tracing.

    Returns a dict with method, path, route, client, user_agent, request_id, traceparent.
    """
    method = request.method
    path = request.url.path
    try:
        route_obj = request.scope.get("route")
        route = getattr(route_obj, "path", path) if route_obj is not None else path
    except Exception:
        route = path
    client = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    traceparent = request.headers.get("traceparent")
    return {
        "method": method,
        "path": path,
        "route": route,
        "client": client,
        "user_agent": ua,
        "request_id": req_id,
        "traceparent": traceparent,
    }


def enrich_response_headers(response: Response, *, request_id: str, traceparent: str | None) -> None:
    """Set correlation headers on the response (best-effort)."""
    try:
        response.headers["x-request-id"] = request_id
        if traceparent:
            response.headers["traceparent"] = traceparent
    except Exception:
        pass


def _current_trace_ids() -> tuple[str | None, str | None]:
    try:
        from core.monitoring.tracing import current_ids as _cur_ids

        return _cur_ids()
    except Exception:
        return None, None


async def request_log_middleware(request: Request, call_next: Callable) -> Response:  # type: ignore[override]
    log = get_logger("medflux.api")
    t0 = time.time()
    meta = extract_request_meta(request)
    try:
        # Create a tracing span for the request
        attributes = {
            "http.route": meta["route"],
            "http.target": meta["path"],
            "http.method": meta["method"],
            "client.ip": meta["client"],
            "user_agent": meta["user_agent"],
            "request_id": meta["request_id"],
        }
        async with _span_ctx(span("http.request", attributes=attributes)) as _:
            response = await call_next(request)
            status = response.status_code
            enrich_response_headers(response, request_id=meta["request_id"], traceparent=meta["traceparent"])
            # annotate current span with status code if tracing is active
            try:
                from opentelemetry import trace as _trace  # lazy import

                _trace.get_current_span().set_attribute("http.status_code", int(status))
            except Exception:
                pass
    except Exception as exc:
        status = 500
        # Try to enrich with current trace_id/span_id if available
        _tid, _sid = _current_trace_ids()
        log.error(
            "request error",
            extra={
                "method": meta["method"],
                "path": meta["path"],
                "client": meta["client"],
                "user_agent": meta["user_agent"],
                "request_id": meta["request_id"],
                "traceparent": meta["traceparent"],
                "trace_id": _tid,
                "span_id": _sid,
                "error": str(exc),
            },
        )
        # Return JSON error with correlation headers
        from fastapi.responses import JSONResponse

        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": meta["request_id"]},
        )
        enrich_response_headers(response, request_id=meta["request_id"], traceparent=meta["traceparent"])
    finally:
        dt = int((time.time() - t0) * 1000)
        try:
            observe_api_request(meta["path"], meta["method"], status, float(dt))
        except Exception:
            pass
        # Enrich with current trace identifiers for log correlation
        _tid, _sid = _current_trace_ids()
        log.info(
            "request",
            extra={
                "method": meta["method"],
                "path": meta["path"],
                "route": meta["route"],
                "client": meta["client"],
                "user_agent": meta["user_agent"],
                "request_id": meta["request_id"],
                "traceparent": meta["traceparent"],
                "trace_id": _tid,
                "span_id": _sid,
                "status": status,
                "latency_ms": dt,
            },
        )
    return response


from contextlib import asynccontextmanager


@asynccontextmanager
async def _span_ctx(cm):
    try:
        with cm:
            yield
    finally:
        pass
