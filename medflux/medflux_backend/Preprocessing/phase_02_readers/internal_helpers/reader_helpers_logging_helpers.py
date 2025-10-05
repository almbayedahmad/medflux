from __future__ import annotations

"""Structured logging helpers for the readers runtime."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from main_helpers.logger import log_event


def record_readers_warning(log_path: Path, warnings: List[str], code: str) -> None:
    """Append a warning code and emit it through the structured logger."""

    if code not in warnings:
        warnings.append(code)
    log_event(log_path, stage="warning", code=code)


def record_readers_tool_event(
    log_path: Path,
    tool_events: List[Dict[str, Any]],
    *,
    step: str,
    status: str,
    page: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record a runtime tool event and return the emitted payload."""

    entry: Dict[str, Any] = {"step": step, "status": status}
    if page is not None:
        entry["page"] = int(page)
    if details:
        entry["details"] = details
    tool_events.append(entry)

    meta: Dict[str, Any] = {}
    if page is not None:
        meta["page"] = int(page)
    if details:
        filtered = {k: v for k, v in details.items() if k not in {"text", "content"}}
        if filtered:
            meta["details"] = filtered
    log_event(log_path, stage=step, code=status, meta=meta or None)
    return entry


# Backwards-compatible aliases
record_warning = record_readers_warning
record_tool_event = record_readers_tool_event


__all__ = [
    "record_readers_warning",
    "record_readers_tool_event",
    "record_warning",
    "record_tool_event",
]
