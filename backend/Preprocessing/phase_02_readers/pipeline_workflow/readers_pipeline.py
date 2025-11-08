from __future__ import annotations

"""Pipeline orchestration for the readers stage.

This module keeps the legacy public API and delegates execution to the new
PhaseRunner-based implementation in `backend.Preprocessing.phase_02_readers.api`.
"""

from typing import Any, Dict, Sequence

from core.validation import validate_io
from core.validation.decorators import payload_from_args
from ..api import run_readers


_STAGE_NAME = "readers"


def process_readers_merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compat helper for callers using this util (no-op change)."""
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = process_readers_merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


@validate_io(
    "phase_02_readers",
    validate_input_enabled=True,
    validate_output_enabled=True,
    soft=False,
    input_getter=payload_from_args(run_id_kw="run_id", items_pos=0),
    output_getter=lambda res: {k: res.get(k) for k in ("run_id","items","stage_stats","versioning")},
)
def run_readers_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    stage_name: str = _STAGE_NAME,
    config_overrides: Dict[str, Any] | None = None,
    run_metadata: Dict[str, Any] | None = None,
    run_id: str | None = None,
) -> Dict[str, Any]:
    # Delegate to the standardized runner while preserving the return shape.
    # run_metadata is currently ignored; the runner computes it internally to
    # match legacy behavior. If explicitly provided, we could thread it later.
    return run_readers(
        generic_items=generic_items,
        config_overrides=config_overrides,
        run_id=run_id,
        stage_name=stage_name,
    )
