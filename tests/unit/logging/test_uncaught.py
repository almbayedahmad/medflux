from __future__ import annotations

import logging
import sys

import pytest

from core.logging.uncaught import install_uncaught_hook


@pytest.mark.unit
def test_uncaught_hook_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    install_uncaught_hook()

    # Simulate an uncaught exception via sys.excepthook
    try:
        raise RuntimeError("kaboom")
    except Exception as exc:
        exc_type, exc_value, exc_tb = sys.exc_info()
        assert exc_type is not None and exc_tb is not None
        sys.excepthook(exc_type, exc_value, exc_tb)

    # Verify a log record was emitted by the uncaught logger
    records = [r for r in caplog.records if r.name == "medflux.uncaught" and r.levelno >= logging.ERROR]
    assert records, "no uncaught error record captured"
    msg = records[-1].getMessage()
    assert "Uncaught exception" in msg

