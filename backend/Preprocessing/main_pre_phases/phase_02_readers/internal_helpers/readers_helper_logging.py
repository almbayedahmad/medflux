from __future__ import annotations

"""Structured logging helpers for the readers runtime."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging import emit_json_event, log_code
from backend.Preprocessing.main_pre_helpers.main_pre_helpers_logger import log_event as _compat_log_event


def record_readers_warning(log_path: Path, warnings: List[str], code: str) -> None:
    """Emit a warning code via centralized logging and keep in-memory record.

    Parameters kept for compatibility; `log_path` is ignored.
    """

    if code not in warnings:
        warnings.append(code)
    log_code(code, level="WARNING", stage="readers")


def record_readers_tool_event(
    log_path: Path,
    tool_events: List[Dict[str, Any]],
    *,
    step: str,
    status: str,
    page: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record a runtime tool event (in-memory list) and emit via centralized logging.

    Parameters kept for compatibility; `log_path` is ignored.
    """

    entry: Dict[str, Any] = {"step": step, "status": status}
    if page is not None:
        entry["page"] = int(page)
    if details:
        entry["details"] = details
    tool_events.append(entry)

    payload: Dict[str, Any] = {"stage": "readers", "step": step, "status": status}
    if page is not None:
        payload["page"] = int(page)
    if details:
        filtered = {k: v for k, v in details.items() if k not in {"text", "content"}}
        if filtered:
            payload.update(filtered)
    emit_json_event(**payload)
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
