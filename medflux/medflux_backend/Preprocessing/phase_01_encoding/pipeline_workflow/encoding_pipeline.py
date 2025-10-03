from __future__ import annotations

"""Pipeline workflow orchestrator for the encoding stage."""

import time
from typing import Any, Dict, Sequence

from ..connecters.encoding_config_connector import connect_encoding_config_connector
from ..connecters.encoding_upstream_connector import connect_encoding_upstream_connector
from ..core_processors.encoding_normalization_process import process_encoding_stage
from ..outputs.encoding_output import save_encoding_doc, save_encoding_stats


def _merge_encoding_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def run_encoding_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    stage_name: str = "encoding",
    config_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    cfg = connect_encoding_config_connector(stage_name)
    if config_overrides:
        cfg = _merge_encoding_config(cfg, config_overrides)

    upstream_items = connect_encoding_upstream_connector(generic_items)

    payload = process_encoding_stage(
        upstream_items,
        detection_cfg=cfg.get("detection"),
        normalization_cfg=cfg.get("normalization"),
    )

    stage_stats = payload["stage_stats"]
    stage_stats.setdefault("generated_at_ms", int(time.time() * 1000))

    save_encoding_doc(payload["unified_document"], cfg)
    save_encoding_stats(stage_stats, cfg)

    return {
        "config": cfg,
        **payload,
    }
