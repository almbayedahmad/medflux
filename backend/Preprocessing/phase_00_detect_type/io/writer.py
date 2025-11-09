# PURPOSE:
#   IO writers for phase_00_detect_type (v2 layout).
#
# OUTCOME:
#   Persist unified document and stage stats JSON to configured paths with
#   artifact stamping, without relying on legacy outputs modules.
#
# INPUTS:
#   - unified_document: Mapping to serialize.
#   - stage_stats: Mapping to serialize.
#   - cfg: Config mapping containing io.out_doc_path and io.out_stats_path.
#
# OUTPUTS:
#   - Files written to the configured paths; returns Path objects.

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


def save_detect_type_doc(unified_document: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    out_path = Path(cfg["io"]["out_doc_path"])  # type: ignore[index]
    return _write_json_with_stamp(unified_document, out_path, schema="phase_00_detect_type_output")


def save_detect_type_stats(stage_stats: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    out_path = Path(cfg["io"]["out_stats_path"])  # type: ignore[index]
    return _write_json_with_stamp(stage_stats, out_path, schema="phase_00_detect_type_output")


__all__ = ["save_detect_type_doc", "save_detect_type_stats"]
