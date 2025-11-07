from __future__ import annotations

import logging
import time as _time

import pytest

from core.logging.filters import DuplicateFilter, RateLimitFilter, SamplingFilter


@pytest.mark.unit
def test_sampling_filter_every_n(monkeypatch: pytest.MonkeyPatch) -> None:
    f = SamplingFilter(n=3)
    rec = logging.LogRecord("medflux", logging.INFO, __file__, 1, "msg", (), None)
    kept = 0
    for _ in range(10):
        if f.filter(rec):
            kept += 1
    # 10 records with n=3 should keep 3 or 4 depending on phase; exact 3 here (indexes 3,6,9)
    assert kept == 3


@pytest.mark.unit
def test_rate_limit_filter_window(monkeypatch: pytest.MonkeyPatch) -> None:
    # Fix time progression deterministically
    t0 = 1000.0
    cur = {"t": t0}

    def fake_time() -> float:
        return cur["t"]

    monkeypatch.setattr("core.logging.filters.time.time", fake_time)
    f = RateLimitFilter(window_s=2, max_events=2)
    rec = logging.LogRecord("medflux", logging.INFO, __file__, 1, "msg", (), None)
    # First two allowed
    assert f.filter(rec) is True
    assert f.filter(rec) is True
    # Third within same window denied
    assert f.filter(rec) is False
    # Advance window, should reset
    cur["t"] = t0 + 2.1
    assert f.filter(rec) is True


@pytest.mark.unit
def test_duplicate_filter_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    # Fix time progression
    t0 = 2000.0
    cur = {"t": t0}

    def fake_time() -> float:
        return cur["t"]

    monkeypatch.setattr("core.logging.filters.time.time", fake_time)
    f = DuplicateFilter(ttl_s=1.0)
    # Same message twice -> second suppressed
    r1 = logging.LogRecord("medflux", logging.WARNING, __file__, 1, "dup", (), None)
    r2 = logging.LogRecord("medflux", logging.WARNING, __file__, 1, "dup", (), None)
    assert f.filter(r1) is True
    assert f.filter(r2) is False
    # Advance beyond TTL -> allowed again
    cur["t"] = t0 + 1.1
    r3 = logging.LogRecord("medflux", logging.WARNING, __file__, 1, "dup", (), None)
    assert f.filter(r3) is True
