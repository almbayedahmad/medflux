# PURPOSE:
#   IO writers for phase_05_light_normalization (v2 scaffold implementation).
#   Persists unified document and stage stats JSON to configured paths.
#
# OUTCOME:
#   Writes JSON outputs with artifact stamping, keeping behavior consistent
#   with earlier phases.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from core.versioning import make_artifact_stamp


def _write_json_with_stamp(payload: Dict[str, Any], destination: Path, *, schema: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = dict(payload)
    data.update(make_artifact_stamp(schema_name=schema))
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def save_light_normalization_doc(unified_document: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    out_path = Path(cfg["io"]["out_doc_path"])  # type: ignore[index]
    return _write_json_with_stamp(unified_document, out_path, schema="phase_05_light_normalization_output")


def save_light_normalization_stats(stage_stats: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    out_path = Path(cfg["io"]["out_stats_path"])  # type: ignore[index]
    return _write_json_with_stamp(stage_stats, out_path, schema="phase_05_light_normalization_output")


__all__ = ["save_light_normalization_doc", "save_light_normalization_stats"]
