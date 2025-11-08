from __future__ import annotations

"""Pipeline workflow orchestrator for the encoding stage.

This module preserves the legacy public API while delegating the actual
execution to the standardized PhaseRunner-based implementation in
`backend.Preprocessing.phase_01_encoding.api`.
"""

from typing import Any, Dict, Sequence

from core.validation import validate_io
from core.validation.decorators import payload_from_args
from ..api import run_encoding


def process_encoding_merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Kept for backward compatibility with callers using this util.

    The PhaseRunner path uses the shared config registry merge, but we retain
    this helper to avoid breaking imports.
    """
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


@validate_io(
    "phase_01_encoding",
    validate_input_enabled=True,
    validate_output_enabled=True,
    soft=False,
    input_getter=payload_from_args(run_id_kw="run_id", items_pos=0),
    output_getter=lambda res: {k: res.get(k) for k in ("run_id","unified_document","stage_stats","versioning")},
)
def run_encoding_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    stage_name: str = "encoding",
    config_overrides: Dict[str, Any] | None = None,
    *,
    run_id: str | None = None,
) -> Dict[str, Any]:
    # Delegate to the standardized runner while preserving return shape
    return run_encoding(
        generic_items=generic_items,
        config_overrides=config_overrides,
        run_id=run_id,
        stage_name=stage_name,
    )
