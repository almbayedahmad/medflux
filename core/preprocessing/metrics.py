# PURPOSE:
#   Lightweight observability helpers (context managers) for phase steps and
#   IO operations, delegating to the core monitoring layer when available.
#
# OUTCOME:
#   Consistent timing and event emission across phases with zero hard
#   dependency on monitoring internals.

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


def _observe_step(phase_id: str, step: str, duration_ms: float) -> None:
    try:
        from core.monitoring import observe_phase_step_duration  # type: ignore

        observe_phase_step_duration(phase_id, step, duration_ms)
    except Exception:
        return


def _observe_io(op: str, name: str, duration_ms: float) -> None:
    try:
        from core.monitoring import observe_io_duration  # type: ignore

        observe_io_duration(op, name, duration_ms)
    except Exception:
        return


@contextmanager
def phase_step(name: str) -> Iterator[None]:
    """Measure duration of a phase step and record it if monitoring is present."""

    t0 = perf_counter()
    try:
        yield
    finally:
        _observe_step(*(name.split(".", 1) if "." in name else (name, "step")), (perf_counter() - t0) * 1000.0)


@contextmanager
def io_op(op: str) -> Iterator[None]:
    """Measure duration of an IO operation (read/write)."""

    t0 = perf_counter()
    try:
        yield
    finally:
        _observe_io(op, "generic", (perf_counter() - t0) * 1000.0)
