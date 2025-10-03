from __future__ import annotations

"""Pipeline workflow orchestrator for the detect_type stage."""

import time
from typing import Any, Dict, Sequence

from ..connecters.detect_type_config_connector import connect_detect_type_config_connector
from ..connecters.detect_type_upstream_connector import connect_detect_type_upstream_connector
from ..core_processors.detect_type_classifier_process import process_detect_type_classifier
from ..outputs.detect_type_output import save_detect_type_doc, save_detect_type_stats


def _merge_detect_type_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def run_detect_type_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    stage_name: str = "detect_type",
    config_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute the detect_type stage end-to-end."""

    cfg = connect_detect_type_config_connector(stage_name)
    if config_overrides:
        cfg = _merge_detect_type_config(cfg, config_overrides)

    upstream_items = connect_detect_type_upstream_connector(generic_items)

    detection_payload = process_detect_type_classifier(
        upstream_items,
        detection_overrides=cfg.get("detection"),
    )

    unified_document = detection_payload["unified_document"]
    stage_stats = detection_payload["stage_stats"]
    stage_stats.setdefault("generated_at_ms", int(time.time() * 1000))

    save_detect_type_doc(unified_document, cfg)
    save_detect_type_stats(stage_stats, cfg)

    return {
        "config": cfg,
        "unified_document": unified_document,
        "stage_stats": stage_stats,
        "results": detection_payload["results"],
    }
