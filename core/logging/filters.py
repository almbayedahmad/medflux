from __future__ import annotations

import logging
import os
import time


class SamplingFilter(logging.Filter):
    """Keep 1 out of N log records (for chatty INFO/DEBUG)."""

    def __init__(self, n: int | None = None) -> None:
        super().__init__()
        self.n = int(os.environ.get("MEDFLUX_LOG_SAMPLING_N", "10") if n is None else n)
        self.n = max(1, self.n)
        self._i = 0

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        self._i = (self._i + 1) % self.n
        return self._i == 0


class RateLimitFilter(logging.Filter):
    """Allow at most `max_events` per `window_s` seconds."""

    def __init__(self, window_s: int | None = None, max_events: int | None = None) -> None:
        super().__init__()
        self.window_s = int(os.environ.get("MEDFLUX_LOG_RATE_WINDOW_S", "10") if window_s is None else window_s)
        self.max_events = int(os.environ.get("MEDFLUX_LOG_RATE_MAX_EVENTS", "50") if max_events is None else max_events)
        self._bucket = 0
        self._t0 = time.time()

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        now = time.time()
        if now - self._t0 > self.window_s:
            self._t0 = now
            self._bucket = 0
        self._bucket += 1
        return self._bucket <= self.max_events


class DuplicateFilter(logging.Filter):
    """Suppress identical messages for a short TTL window.

    Keyed by (logger name, level, message, code).
    TTL seconds can be set via MEDFLUX_LOG_DUP_TTL (default 2s).
    """

    def __init__(self, ttl_s: float | None = None) -> None:
        super().__init__()
        try:
            env = float(os.environ.get("MEDFLUX_LOG_DUP_TTL", "2"))
        except Exception:
            env = 2.0
        self.ttl_s = float(env if ttl_s is None else ttl_s)
        self._last: dict[tuple[str, int, str, str | None], float] = {}

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        try:
            code = None
            if isinstance(record.__dict__.get("code"), str):
                code = record.__dict__["code"]  # type: ignore[assignment]
            key = (record.name, record.levelno, record.getMessage(), code)
            now = time.time()
            last = self._last.get(key, 0.0)
            if (now - last) < self.ttl_s:
                return False
            self._last[key] = now
        except Exception:
            return True
        return True
