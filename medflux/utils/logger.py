from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


LOG_ENCODING = "utf-8"


def log_event(path: str | Path, stage: str, code: str, message: str = "", meta: dict[str, Any] | None = None) -> None:
    """Append a structured log event to the given JSONL log file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": time.time(),
        "stage": stage,
        "code": code,
        "message": message,
        "meta": meta or {},
    }
    with target.open("a", encoding=LOG_ENCODING) as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
