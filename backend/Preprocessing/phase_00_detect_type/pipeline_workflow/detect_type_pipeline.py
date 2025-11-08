from __future__ import annotations

"""Pipeline workflow orchestrator for the detect_type stage.

This module retains the legacy public API but delegates execution to the new
PhaseRunner-based implementation in `backend.Preprocessing.phase_00_detect_type.api`.
"""

from typing import Any, Dict, Sequence

from core.validation import validate_io
from core.validation.decorators import payload_from_args
from ..api import run_detect_type


def _merge_detect_type_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Kept for backward compatibility for callers relying on this util."""
    merged: Dict[str, Any] = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


@validate_io(
    "phase_00_detect_type",
    validate_input_enabled=True,
    validate_output_enabled=True,
    soft=False,
    input_getter=payload_from_args(run_id_kw="run_id", items_pos=0),
    output_getter=lambda res: {k: res.get(k) for k in ("run_id","unified_document","stage_stats","versioning")},
)
def run_detect_type_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    stage_name: str = "detect_type",
    config_overrides: Dict[str, Any] | None = None,
    *,
    run_id: str | None = None,
) -> Dict[str, Any]:
    """Execute the detect_type stage end-to-end via the standardized runner."""

    return run_detect_type(
        generic_items=generic_items,
        config_overrides=config_overrides,
        run_id=run_id,
        stage_name=stage_name,
    )
