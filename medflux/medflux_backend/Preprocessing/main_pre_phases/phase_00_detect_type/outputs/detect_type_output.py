from __future__ import annotations

"""Outputs writer for the detect_type stage."""

import json
from pathlib import Path
from typing import Any, Dict


def save_detect_type_doc(unified_document: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    """Persist the unified document payload to the configured path."""

    out_path = Path(cfg["io"]["out_doc_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(unified_document, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def save_detect_type_stats(stage_stats: Dict[str, Any], cfg: Dict[str, Any]) -> Path:
    """Persist the stage statistics payload to the configured path."""

    out_path = Path(cfg["io"]["out_stats_path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stage_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
