from __future__ import annotations

import logging
import sys

import pytest

from core.logging import configure_logging


@pytest.mark.unit
def test_console_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "dev")
    monkeypatch.setenv("MEDFLUX_LOG_TO_STDERR", "1")
    monkeypatch.setenv("MEDFLUX_LOG_FILE", "0")
    # Reset root handlers
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    configure_logging(force=True)
    streams = [getattr(h, "stream", None) for h in logging.getLogger().handlers if isinstance(h, logging.StreamHandler)]
    assert any(s is sys.stderr for s in streams), "expected console stream to be stderr"
