from __future__ import annotations

import json
import re
from pathlib import Path
import os
from typing import Any, Dict, List


_VOLATILE_KEYS = {
    "timestamp",
    "timestamps",
    "created_at",
    "updated_at",
    "run_id",
    "trace_id",
    "span_id",
    "uuid",
}


_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?$")


def _normalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in _VOLATILE_KEYS:
                continue
            out[k] = _normalize(v)
        return out
    if isinstance(obj, list):
        return [_normalize(x) for x in obj]
    if isinstance(obj, str):
        if _ISO_TS_RE.match(obj):
            return "<ts>"
        return obj
    return obj


def assert_json_golden(actual: Any, golden_rel_path: str | Path) -> None:
    base = Path("tests") / "golden"
    golden_path = base / Path(golden_rel_path)
    with golden_path.open("r", encoding="utf-8") as f:
        expected = json.load(f)
    norm_actual = _normalize(actual)
    norm_expected = _normalize(expected)
    if norm_actual != norm_expected:
        if str(os.environ.get("UPDATE_GOLDEN", "")).strip().lower() in {"1", "true", "yes"} and not os.environ.get("CI"):
            golden_path.write_text(
                json.dumps(norm_actual, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return
        assert (
            norm_actual == norm_expected
        ), f"Golden mismatch: {golden_path}.\nExpected: {json.dumps(norm_expected, ensure_ascii=False, indent=2)}\nActual:   {json.dumps(norm_actual, ensure_ascii=False, indent=2)}"
