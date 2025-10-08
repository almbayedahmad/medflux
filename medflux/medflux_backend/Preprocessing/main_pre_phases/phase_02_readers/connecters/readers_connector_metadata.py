from __future__ import annotations

"""Cross-phase metadata connectors for the readers stage."""

from pathlib import Path
from typing import Any, Dict

from medflux_backend.Preprocessing.main_pre_phases.phase_00_detect_type.internal_helpers.detect_type_detection_helper import (
    process_detect_type_file,
)
from medflux_backend.Preprocessing.main_pre_phases.phase_01_encoding.internal_helpers.encoding_detection_helper import (
    get_encoding_text_detection,
)

_DEFAULT_PIPELINE_ID = "preprocessing.readers"


def get_readers_detect_meta(input_path: Path) -> Dict[str, Any]:
    """Get detection metadata from phase_00_detect_type."""
    result = process_detect_type_file(str(input_path))
    recommended = result.recommended or {}
    return {
        "detected_mode": recommended.get("mode"),
        "lang": recommended.get("lang") or "deu+eng",
        "dpi": recommended.get("dpi", 300),
        "psm": recommended.get("psm", 6),
        "tables_mode": recommended.get("tables_mode", "light"),
        "file_type": result.file_type.value,
        "confidence": result.confidence,
        "details": result.details or {},
    }


def get_readers_encoding_meta(input_path: Path, file_type: str) -> Dict[str, Any]:
    """Get encoding metadata from phase_01_encoding."""
    payload: Dict[str, Any] = {
        "primary": None,
        "confidence": None,
        "bom": False,
        "is_utf8": None,
        "sample_len": 0,
    }
    if file_type.lower() in {"txt"}:
        info = get_encoding_text_detection(str(input_path))
        payload.update(
            {
                "primary": info.encoding,
                "confidence": info.confidence,
                "bom": info.bom,
                "is_utf8": info.is_utf8,
                "sample_len": info.sample_len,
            }
        )
    return payload


def compute_readers_run_metadata(run_id: str | None = None, pipeline_id: str | None = None) -> Dict[str, str]:
    """Generate run metadata for the readers stage."""
    from uuid import uuid4

    resolved_run_id = run_id or f"readers-{uuid4().hex}"
    resolved_pipeline = pipeline_id or _DEFAULT_PIPELINE_ID
    return {"run_id": resolved_run_id, "pipeline_id": resolved_pipeline}


__all__ = [
    "get_readers_detect_meta",
    "get_readers_encoding_meta",
    "compute_readers_run_metadata",
]
