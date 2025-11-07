from __future__ import annotations

"""Backward-compatible logging shim for preprocessing helpers.

This module used to append JSONL entries to a file. It now redirects events to
the centralized logging layer (console only for now).
"""

from pathlib import Path
from typing import Any

from core.logging import emit_json_event, log_code


def log_event(path: str | Path, stage: str, code: str, message: str = "", meta: dict[str, Any] | None = None) -> None:
    """Redirect structured log event to the centralized logger (console only).

    Parameters kept for compatibility; `path` is ignored.
    """
    payload: dict[str, Any] = {"stage": stage, "code": code}
    if message:
        payload["message"] = message
    if meta:
        payload.update(meta)
    # Emit as an INFO event; warnings should use `log_code(..., level='WARNING')`
    emit_json_event(**payload)
