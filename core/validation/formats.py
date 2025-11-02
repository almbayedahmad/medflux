from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from jsonschema import FormatChecker


_RUN_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}-[0-9a-fA-F]{8}$")


format_checker = FormatChecker()


@format_checker.checks("uuid")
def _is_uuid(value: object) -> bool:  # noqa: ANN001
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False


@format_checker.checks("path")
def _is_path(value: object) -> bool:  # noqa: ANN001
    return isinstance(value, str) and len(value.strip()) > 0


@format_checker.checks("run-id")
def _is_run_id(value: object) -> bool:  # noqa: ANN001
    return isinstance(value, str) and bool(_RUN_ID_RE.match(value))
