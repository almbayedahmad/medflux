from __future__ import annotations

import logging
import threading
import time

import pytest

from core.logging.uncaught import install_uncaught_hook


@pytest.mark.unit
def test_uncaught_thread_exception_logged(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR)
    install_uncaught_hook()

    def boom():
        raise RuntimeError("thread-boom")

    t = threading.Thread(target=boom)
    t.start()
    t.join()

    errs = [r for r in caplog.records if r.name == "medflux.uncaught" and r.levelno >= logging.ERROR]
    assert errs, "expected uncaught thread exception log"
    assert any("thread-boom" in (getattr(r, "exc", "") or getattr(r, "message", "")) for r in errs)
