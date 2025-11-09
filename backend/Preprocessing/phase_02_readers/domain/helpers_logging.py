# PURPOSE:
#   Structured logging helpers for the readers runtime, migrated from
#   internal_helpers to the domain layer.
#
# OUTCOME:
#   Centralized, PII-safe event logging for readers with in-memory capture of
#   warnings and tool events, independent of legacy package layout.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging import emit_json_event, log_code


def record_readers_warning(log_path: Path, warnings: List[str], code: str) -> None:
    """Emit a warning code and track it in-memory.

    Args:
        log_path: Ignored; kept for interface compatibility.
        warnings: Mutable list where the code will be appended once.
        code: Warning code.
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
    """Record a runtime tool event and emit via centralized logging.

    Args:
        log_path: Ignored; kept for interface compatibility.
        tool_events: Mutable list to append event entry.
        step: Processing step name.
        status: Result status (ok/fallback/etc.).
        page: Optional page number.
        details: Optional JSON-serializable details.
    Returns:
        The recorded event entry.
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
