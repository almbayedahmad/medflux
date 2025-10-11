from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..core_functions.readers_core_meta import compute_readers_doc_meta_payload


def compute_readers_doc_meta(
    *,
    input_path: Path,
    detect_meta: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    readers_result: Dict[str, Any],
    timings: Dict[str, Any],
    run_id: str,
    pipeline_id: str,
) -> Dict[str, Any]:
    """Stage-scoped wrapper to construct readers doc metadata."""
    return compute_readers_doc_meta_payload(
        input_path=input_path,
        detect_meta=detect_meta,
        encoding_meta=encoding_meta,
        readers_result=readers_result,
        timings=timings,
        run_id=run_id,
        pipeline_id=pipeline_id,
    )


__all__ = ["compute_readers_doc_meta"]
