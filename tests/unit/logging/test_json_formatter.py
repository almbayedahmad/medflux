from __future__ import annotations

import json
import logging
import os
import traceback

from core.logging.json_formatter import JSONLogFormatter


def _format(record: logging.LogRecord) -> dict:
    f = JSONLogFormatter()
    line = f.format(record)
    return json.loads(line)


def test_json_formatter_includes_trace_url(monkeypatch):
    monkeypatch.setenv("MEDFLUX_TRACE_URL_TEMPLATE", "http://localhost:3200/trace/{trace_id}")
    rec = logging.LogRecord("medflux", logging.INFO, __file__, 1, "msg", (), None)
    rec.trace_id = "abc123"
    out = _format(rec)
    assert out["trace_url"].endswith("/trace/abc123")


def test_json_formatter_structured_error():
    try:
        raise ValueError("boom")
    except Exception:
        exc = traceback.sys.exc_info()
    rec = logging.LogRecord("medflux", logging.ERROR, __file__, 1, "oops", (), exc)
    out = _format(rec)
    assert out["err"]["type"] == "ValueError"
    assert "boom" in out["err"]["msg"]
    assert "ValueError" in out["err"]["stack"]

