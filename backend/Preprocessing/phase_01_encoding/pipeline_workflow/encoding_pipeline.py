from __future__ import annotations

"""Pipeline workflow orchestrator for the encoding stage."""

import time
from typing import Any, Dict, Sequence

from ..connecters.encoding_connector_config import connect_encoding_config_connector
from ..connecters.encoding_connector_upstream import connect_encoding_upstream_connector
from ..core_functions.encoding_core_normalizer import process_encoding_stage
from ..outputs.encoding_output import save_encoding_doc, save_encoding_stats
from core.validation import validate_io
from core.validation.decorators import payload_from_args
from core.versioning import make_artifact_stamp
from core.monitoring import observe_phase_step_duration, observe_io_duration, record_io_error
import time as _time


def process_encoding_merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
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
    cfg = connect_encoding_config_connector(stage_name)
    if config_overrides:
        cfg = process_encoding_merge_config(cfg, config_overrides)

    upstream_items = connect_encoding_upstream_connector(generic_items)

    _t0 = _time.perf_counter()
    payload = process_encoding_stage(
        upstream_items,
        detection_cfg=cfg.get("detection"),
        normalization_cfg=cfg.get("normalization"),
    )
    observe_phase_step_duration("phase_01_encoding", "process", (_time.perf_counter() - _t0) * 1000.0)

    stage_stats = payload["stage_stats"]
    stage_stats.setdefault("generated_at_ms", int(time.time() * 1000))

    try:
        io_t0 = _time.perf_counter()
        save_encoding_doc(payload["unified_document"], cfg)
        observe_io_duration("write", "encoding_doc", (_time.perf_counter() - io_t0) * 1000.0)
    except Exception:
        record_io_error("write", "encoding_doc")
        raise
    try:
        io_t0 = _time.perf_counter()
        save_encoding_stats(stage_stats, cfg)
        observe_io_duration("write", "encoding_stats", (_time.perf_counter() - io_t0) * 1000.0)
    except Exception:
        record_io_error("write", "encoding_stats")
        raise

    result: Dict[str, Any] = {
        "config": cfg,
        **payload,
    }
    if run_id:
        result["run_id"] = run_id
    result.update(make_artifact_stamp(schema_name="phase_01_encoding_output"))
    return result
