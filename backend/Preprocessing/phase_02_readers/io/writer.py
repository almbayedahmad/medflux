# PURPOSE:
#   IO writers for phase_02_readers (v2 layout implementation).
#   Implements file persistence for doc meta, stage stats, and summary.
#
# OUTCOME:
#   Writes JSON outputs to configured paths with artifact stamping while
#   maintaining compatibility with legacy pipeline expectations.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.versioning import make_artifact_stamp


def _write_json_with_stamp(payload: Dict[str, Any], destination: Path, schema: str = "stage_contract") -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = dict(payload)
    data.update(make_artifact_stamp(schema_name=schema))
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def save_readers_doc_meta(doc_meta: Dict[str, Any], out_path: Path) -> Path:
    return _write_json_with_stamp(doc_meta, out_path, schema="readers_doc_meta")


def save_readers_stage_stats(stats: Dict[str, Any], out_path: Path) -> Path:
    return _write_json_with_stamp(stats, out_path, schema="readers_stage_stats")


def save_readers_summary(summary: Dict[str, Any], out_path: Path) -> Path:
    return _write_json_with_stamp(summary, out_path, schema="readers_summary")


__all__ = ["save_readers_doc_meta", "save_readers_stage_stats", "save_readers_summary"]
