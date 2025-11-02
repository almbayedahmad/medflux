from __future__ import annotations

import json
from typing import Any, Mapping


def validate_log_record(payload: Mapping[str, Any]) -> bool:
    """Very light validation for tests: ensure core fields are present.

    Not a strict schema; just a smoke check.
    """
    try:
        _ = json.dumps(payload)
    except Exception:
        return False
    for k in ("level", "logger", "message"):
        if k not in payload:
            return False
    return True
