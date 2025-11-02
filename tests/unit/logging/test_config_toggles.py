from __future__ import annotations

import logging
import os

import pytest

from core.logging import configure_logging
from core.logging.json_formatter import JSONLogFormatter


@pytest.mark.unit
def test_console_json_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "dev")
    monkeypatch.setenv("MEDFLUX_LOG_JSON", "1")
    monkeypatch.setenv("MEDFLUX_LOG_FILE", "0")
    # Reset root handlers
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    configure_logging(force=True)
    # Expect a StreamHandler with JSON formatter
    fmts = [getattr(h, "formatter", None) for h in logging.getLogger().handlers]
    assert any(isinstance(f, JSONLogFormatter) for f in fmts if f is not None), "console JSON formatter not applied"


@pytest.mark.unit
def test_disable_file_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "dev")
    monkeypatch.setenv("MEDFLUX_LOG_FILE", "0")
    # Reset root handlers
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    configure_logging(force=True)
    # Ensure no rotating file handler is present
    assert not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logging.getLogger().handlers)

