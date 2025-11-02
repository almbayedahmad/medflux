from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict


_SKIP_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "message",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JSONLogFormatter(logging.Formatter):
    """Minimal JSON formatter for structured logs.

    Use with logging.config.dictConfig via:
      formatters:
        json:
          '()': core.logging.json_formatter.JSONLogFormatter
    """

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": int(record.created * 1000),
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Optional trace URL enrichment if trace_id present and template configured
        try:
            trace_id = getattr(record, "trace_id", None)
            tmpl = os.environ.get("MEDFLUX_TRACE_URL_TEMPLATE", "").strip()
            if trace_id and tmpl:
                try:
                    payload["trace_url"] = tmpl.format(trace_id=trace_id)
                except Exception:
                    # Fallback to appending trace_id
                    payload["trace_url"] = f"{tmpl.rstrip('/')}/{trace_id}"
        except Exception:
            pass
        # Exceptions: add structured error fields
        try:
            if record.exc_info:
                etype = record.exc_info[0].__name__ if record.exc_info[0] else None
                evalue = str(record.exc_info[1]) if record.exc_info[1] else None
                import traceback as _tb

                estack = "".join(_tb.format_exception(*record.exc_info))
                payload["err"] = {"type": etype, "msg": evalue, "stack": estack}
        except Exception:
            pass

        # Merge extras, skipping known logging fields; apply truncation
        truncated_any = False
        for k, v in record.__dict__.items():
            if k in _SKIP_KEYS:
                continue
            try:
                # string truncation safeguard
                if isinstance(v, str) and len(v) > 4096:
                    payload[k] = v[:4096]
                    truncated_any = True
                else:
                    json.dumps(v)
                    payload[k] = v
            except Exception:
                payload[k] = repr(v)
                truncated_any = True
        if truncated_any and "truncated" not in payload:
            payload["truncated"] = True
        return json.dumps(payload, ensure_ascii=False)
