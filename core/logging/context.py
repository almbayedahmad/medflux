from __future__ import annotations

import contextvars
import logging
import os
import socket
from typing import Any, Dict


_ctx: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("medflux_log_ctx", default={})


def set_ctx(**fields: Any) -> None:
    cur = dict(_ctx.get())
    cur.update({k: v for k, v in fields.items() if v is not None})
    _ctx.set(cur)


def clear_ctx() -> None:
    _ctx.set({})


def get_ctx() -> Dict[str, Any]:
    return dict(_ctx.get())


class ContextFilter(logging.Filter):
    """Inject contextvars into every log record.

    Adds hostname/pid if not present.
    Optionally adds app_version if available via core.versioning.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        try:
            for k, v in get_ctx().items():
                if k not in record.__dict__:
                    record.__dict__[k] = v
            # Try to auto-inject trace/span ids when tracing is active
            if "trace_id" not in record.__dict__:
                try:
                    from core.monitoring.tracing import current_ids  # lazy import

                    tid, sid = current_ids()
                    if tid and "trace_id" not in record.__dict__:
                        record.__dict__["trace_id"] = tid
                        record.__dict__.setdefault("span_id", sid)
                except Exception:
                    pass
            # Host/pid defaults
            record.__dict__.setdefault("hostname", socket.gethostname())
            record.__dict__.setdefault("pid", os.getpid())
            # App version (best effort)
            if "app_version" not in record.__dict__:
                try:
                    from core.versioning import get_version

                    record.__dict__["app_version"] = get_version()
                except Exception:
                    pass
        except Exception:
            pass
        return True
