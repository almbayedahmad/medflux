# PURPOSE:
#   IO writers for phase_01_encoding (v2 layout implementation).
#   Implements file persistence for unified document and stage stats.
#
# OUTCOME:
#   Writes JSON outputs to configured paths with artifact stamping while
#   maintaining compatibility with legacy pipeline expectations.
#
# INPUTS:
#   - unified_document: Dict produced by domain.process
#   - stage_stats: Dict produced by domain.process
#   - cfg: Loaded stage configuration with io.out_doc_path/out_stats_path
#
# OUTPUTS:
#   - Files written to disk at the configured locations; returns Path to each.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.versioning import make_artifact_stamp


def save_encoding_doc(unified_document: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    """Persist the unified document JSON to the configured output path.

    Args:
        unified_document: The aggregated encoding stage document.
        cfg: Stage configuration mapping with 'io.out_doc_path'.
    Returns:
        Path to the written document file.
    Outcome:
        Durable artifact for downstream consumption and auditing.
    """

    out_path = Path(cfg["io"]["out_doc_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(unified_document)
    payload.update(make_artifact_stamp(schema_name="phase_01_encoding_output"))
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def save_encoding_stats(stage_stats: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    """Persist the stage statistics JSON to the configured output path.

    Args:
        stage_stats: The computed stage statistics mapping.
        cfg: Stage configuration mapping with 'io.out_stats_path'.
    Returns:
        Path to the written stats file.
    Outcome:
        Durable metrics artifact for monitoring and analysis.
    """

    out_path = Path(cfg["io"]["out_stats_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(stage_stats)
    payload.update(make_artifact_stamp(schema_name="phase_01_encoding_output"))
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


__all__ = ["save_encoding_doc", "save_encoding_stats"]
