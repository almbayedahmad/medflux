# PURPOSE:
#   Expose readers metadata helpers via the connectors package for v2 layout.
# OUTCOME:
#   Provides stable functions to fetch detection/encoding metadata and compute
#   run metadata while delegating cross-phase logic to services.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from core.preprocessing.services.readers import ReadersService


def get_readers_detect_meta(input_path: Path) -> Dict[str, Any]:
    """Get detection-derived metadata for readers stage.

    Args:
        input_path: Path to input document.
    Returns:
        Mapping with detected_mode, lang, dpi, psm, tables_mode, file_type, confidence, details.
    Outcome:
        Normalized detection hints for readers parameterization.
    """

    return ReadersService.get_detect_meta(input_path)


def get_readers_encoding_meta(input_path: Path, file_type: str) -> Dict[str, Any]:
    """Get encoding-related metadata for readers stage when relevant.

    Args:
        input_path: Path to input document (text file for encoding checks).
        file_type: File type hint (e.g., 'txt').
    Returns:
        Mapping with text encoding insights when applicable.
    Outcome:
        Supplies encoding hints for readers decisions (e.g., line parsing).
    """

    return ReadersService.get_encoding_meta(input_path, file_type)


def compute_readers_run_metadata(run_id: str | None = None, pipeline_id: str | None = None) -> Dict[str, str]:
    """Compute run metadata for readers stage via service facade.

    Args:
        run_id: Optional pre-specified run identifier.
        pipeline_id: Optional pipeline identifier.
    Returns:
        Mapping with run_id and pipeline_id.
    Outcome:
        Stable identifiers for logging and output paths generation.
    """

    return ReadersService.compute_run_metadata(run_id=run_id, pipeline_id=pipeline_id)


__all__ = [
    "get_readers_detect_meta",
    "get_readers_encoding_meta",
    "compute_readers_run_metadata",
]
