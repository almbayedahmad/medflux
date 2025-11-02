from __future__ import annotations

import logging

from core.logging.context import ContextFilter, clear_ctx, set_ctx


def test_context_filter_injects_fields():
    try:
        clear_ctx()
    except Exception:
        pass
    set_ctx(run_id="RID", phase="phase_x")
    rec = logging.LogRecord(
        name="medflux.test.ctx",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    f = ContextFilter()
    assert f.filter(rec) is True
    # Context values
    assert getattr(rec, "run_id") == "RID"
    assert getattr(rec, "phase") == "phase_x"
    # Defaults
    assert getattr(rec, "hostname")
    assert getattr(rec, "pid") > 0
    # App version injected
    assert getattr(rec, "app_version")

