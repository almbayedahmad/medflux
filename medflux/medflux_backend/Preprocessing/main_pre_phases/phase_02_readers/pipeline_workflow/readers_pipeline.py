from __future__ import annotations

"""Pipeline orchestration for the readers stage."""

from pathlib import Path
from typing import Any, Dict, Sequence

from ..connecters.readers_connector_config import connect_readers_config_connector
from ..connecters.readers_connector_upstream import connect_readers_upstream_connector
from ..core_functions.readers_core_process import process_readers_segment
from ..connecters.readers_connector_metadata import compute_readers_run_metadata
from ..outputs.readers_output import (
    save_readers_doc_meta,
    save_readers_stage_stats,
    save_readers_summary,
)


_STAGE_NAME = "readers"


def process_readers_merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = process_readers_merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def run_readers_pipeline(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    stage_name: str = _STAGE_NAME,
    config_overrides: Dict[str, Any] | None = None,
    run_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    config = connect_readers_config_connector(stage_name)
    if config_overrides:
        config = process_readers_merge_config(config, config_overrides)

    upstream_items = connect_readers_upstream_connector(generic_items)

    io_config = dict(config.get("io") or {})
    options_config = dict(config.get("options") or {})
    run_meta = dict(run_metadata or compute_readers_run_metadata())

    payload = process_readers_segment(
        upstream_items,
        io_config=io_config,
        options_config=options_config,
        run_metadata=run_meta,
    )

    out_doc_path = Path(io_config.get("out_doc_path") or (Path(io_config.get("out_root", ".")) / "readers_doc_meta.json"))
    out_stats_path = Path(io_config.get("out_stats_path") or (Path(io_config.get("out_root", ".")) / "readers_stage_stats.json"))
    out_summary_path = Path(io_config.get("out_summary_path") or (Path(io_config.get("out_root", ".")) / "readers_summary.json"))

    doc_meta_payload = {"documents": [item["doc_meta"] for item in payload["items"]]}
    save_readers_doc_meta(doc_meta_payload, out_doc_path)
    save_readers_stage_stats(payload["stage_stats"], out_stats_path)
    save_readers_summary(payload["summary"], out_summary_path)

    return {
        "config": config,
        "items": payload["items"],
        "stage_stats": payload["stage_stats"],
        "summary": payload["summary"],
        "io": {
            "out_doc_path": str(out_doc_path),
            "out_stats_path": str(out_stats_path),
            "out_summary_path": str(out_summary_path),
        },
    }
