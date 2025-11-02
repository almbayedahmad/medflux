from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import pytest

from core.logging import configure_logging
from core.logging.queue_setup import stop_queue


@pytest.mark.unit
def test_prod_daily_rotation_and_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    # Use prod profile where json_file_daily handler is defined
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "prod")
    monkeypatch.setenv("MEDFLUX_LOG_DAILY", "1")
    # Ensure file handler is not disabled
    monkeypatch.delenv("MEDFLUX_LOG_FILE", raising=False)
    # Point log root to a temp dir under cwd to avoid permission issues
    tmp_root = Path("logs_test_daily")
    monkeypatch.setenv("MEDFLUX_LOG_ROOT", str(tmp_root))

    # Reset root handlers
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    configure_logging(force=True)

    # In prod, queue is attached; get effective handlers behind it
    try:
        from core.logging.queue_setup import effective_handlers  # type: ignore

        handlers = list(effective_handlers())
    except Exception:
        handlers = list(logging.getLogger().handlers)

    # Expect a TimedRotatingFileHandler among effective handlers
    assert any(isinstance(h, logging.handlers.TimedRotatingFileHandler) for h in handlers)
    # Verify the file is anchored under MEDFLUX_LOG_ROOT and created
    file_handlers = [h for h in handlers if isinstance(h, (logging.handlers.RotatingFileHandler, logging.handlers.TimedRotatingFileHandler))]
    assert file_handlers, "no file handlers found"
    for fh in file_handlers:
        p = Path(getattr(fh, "baseFilename", ""))
        # File anchored under MEDFLUX_LOG_ROOT; compare folder name for portability
        assert p.parent.name == tmp_root.name
        assert p.parent.exists()
    # Cleanup queue listener
    stop_queue()


@pytest.mark.unit
def test_prod_queue_attached_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "prod")
    # default MEDFLUX_LOG_ENABLE_QUEUE=1
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    configure_logging(force=True)
    # Root should have a QueueHandler only
    assert root.handlers, "root has no handlers"
    assert isinstance(root.handlers[0], logging.handlers.QueueHandler)
    stop_queue()
