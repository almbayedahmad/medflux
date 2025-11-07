from __future__ import annotations

"""Pipeline workflow orchestrator for the detect_type stage."""

import time
from typing import Any, Dict, Sequence

from ..connecters.detect_type_connector_config import connect_detect_type_config_connector
from ..connecters.detect_type_connector_upstream import connect_detect_type_upstream_connector
from ..core_functions.detect_type_core_classifier import process_detect_type_classifier
from ..outputs.detect_type_output import save_detect_type_doc, save_detect_type_stats
from core.validation import validate_io
from core.validation.decorators import payload_from_args
from core.versioning import make_artifact_stamp
from core.monitoring import observe_phase_step_duration, observe_io_duration, record_io_error
import time as _time


def _merge_detect_type_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
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
    """Execute the detect_type stage end-to-end."""

    cfg = connect_detect_type_config_connector(stage_name)
    if config_overrides:
        cfg = _merge_detect_type_config(cfg, config_overrides)

    upstream_items = connect_detect_type_upstream_connector(generic_items)

    t0 = _time.perf_counter()
    detection_payload = process_detect_type_classifier(
        upstream_items,
        detection_overrides=cfg.get("detection"),
    )
    observe_phase_step_duration("phase_00_detect_type", "classifier", (_time.perf_counter() - t0) * 1000.0)

    unified_document = detection_payload["unified_document"]
    stage_stats = detection_payload["stage_stats"]
    stage_stats.setdefault("generated_at_ms", int(time.time() * 1000))

    try:
        io_t0 = _time.perf_counter()
        save_detect_type_doc(unified_document, cfg)
        observe_io_duration("write", "detect_type_doc", (_time.perf_counter() - io_t0) * 1000.0)
    except Exception:
        record_io_error("write", "detect_type_doc")
        raise
    try:
        io_t0 = _time.perf_counter()
        save_detect_type_stats(stage_stats, cfg)
        observe_io_duration("write", "detect_type_stats", (_time.perf_counter() - io_t0) * 1000.0)
    except Exception:
        record_io_error("write", "detect_type_stats")
        raise

    payload: Dict[str, Any] = {
        "config": cfg,
        "unified_document": unified_document,
        "stage_stats": stage_stats,
        "results": detection_payload["results"],
    }
    if run_id:
        payload["run_id"] = run_id
    payload.update(make_artifact_stamp(schema_name="phase_00_detect_type_output"))
    return payload
