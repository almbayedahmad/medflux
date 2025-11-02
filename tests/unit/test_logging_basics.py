from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import pytest

from core.logging import get_logger, with_context, configure_log_destination, configure_logging


@pytest.mark.unit
def test_get_logger_respects_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDFLUX_LOG_LEVEL", "DEBUG")
    # Reset root handlers to force fresh config
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    logger = get_logger("test.logger")
    assert logger is not None
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


@pytest.mark.unit
def test_with_context_merges_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure simple stream handler is configured
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    configure_logging(force=True)

    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
            records.append(record)

    cap = Capture()
    logging.getLogger().addHandler(cap)
    try:
        adapter = with_context(get_logger("ctx.test"), request_id="req-123")
        adapter.info("hello", extra={"user": "u1"})
        assert records, "no record captured"
        rec = records[-1]
        # Extra fields become attributes on the LogRecord
        assert getattr(rec, "request_id", None) == "req-123"
        assert getattr(rec, "user", None) == "u1"
    finally:
        logging.getLogger().removeHandler(cap)


@pytest.mark.unit
def test_configure_log_destination_builds_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Force basic logging, ensure no file handlers are required for usage
    configure_logging(force=True)
    run_id = "20250101T120000-deadbeef"
    phase = "phase_demo"
    flow = "flowA"
    dest = configure_log_destination(run_id, phase, flow=flow, root=tmp_path)
    assert dest.name == f"{phase}.jsonl"
    # Expect day/run_id nesting
    day = datetime.utcnow().strftime("%Y-%m-%d")
    assert dest.parent.name == run_id
    assert dest.parent.parent.name == day or dest.parent.parent.name == flow
    # Depending on flow, check directory parts
    parts = dest.relative_to(tmp_path).parts
    if flow in parts:
        # flow/day/run_id/phase.jsonl
        assert parts[0] == flow
        assert parts[2] == run_id
    else:
        # day/run_id/phase.jsonl
        assert parts[0] == day
        assert parts[1] == run_id
