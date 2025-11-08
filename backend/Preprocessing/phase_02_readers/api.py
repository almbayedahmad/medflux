# PURPOSE:
#   Phase 02 (readers) public API and PhaseRunner implementation.
#   Wraps existing connectors and domain logic into a standardized lifecycle
#   while preserving the legacy orchestrator entry point.
#
# OUTCOME:
#   Consistent, testable readers phase with stable inputs/outputs and minimal
#   divergence from the existing behavior.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from core.preprocessing.config.registry import (
    get_phase_config,
    merge_overrides,
    register_phase_config,
)
from core.preprocessing.phase_api import PhaseRunner, PhaseSpec
from core.preprocessing.metrics import io_op
from core.versioning import make_artifact_stamp

from .connecters.readers_connector_config import connect_readers_config_connector
from .connecters.readers_connector_upstream import connect_readers_upstream_connector
from .core_functions.readers_core_process import process_readers_segment
from .connecters.readers_connector_metadata import compute_readers_run_metadata
from .outputs.readers_output import (
    save_readers_doc_meta,
    save_readers_stage_stats,
    save_readers_summary,
)


PHASE_ID = "phase_02_readers"
PHASE_NAME_DEFAULT = "readers"


def _registry_loader(_profile: Optional[str]) -> Dict[str, Any]:
    return connect_readers_config_connector(PHASE_NAME_DEFAULT)


try:
    register_phase_config(PHASE_ID, _registry_loader)
except Exception:
    pass


class ReadersRunner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    """Standardized runner for readers phase."""

    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = get_phase_config(self.spec.phase_id) or connect_readers_config_connector(self.spec.name)
        return merge_overrides(cfg, overrides)

    def _connect_upstream(self, items: Optional[Sequence[Dict[str, Any]]] = None) -> Sequence[Dict[str, Any]]:
        return connect_readers_upstream_connector(items)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        io_config = dict(config.get("io") or {})
        options_config = dict(config.get("options") or {})
        run_meta = compute_readers_run_metadata()
        payload = process_readers_segment(
            upstream,
            io_config=io_config,
            options_config=options_config,
            run_metadata=run_meta,
        )
        # Add resolved io and run metadata into payload for saving to follow the same behavior
        payload["_io_config"] = io_config
        payload["_run_meta"] = run_meta
        return payload

    def _save_outputs(self, payload: Dict[str, Any], *, config: Dict[str, Any]) -> None:
        io_config = dict(payload.get("_io_config") or (config.get("io") or {}))
        out_doc_path = Path(io_config.get("out_doc_path") or (Path(io_config.get("out_root", ".")) / "readers_doc_meta.json"))
        out_stats_path = Path(io_config.get("out_stats_path") or (Path(io_config.get("out_root", ".")) / "readers_stage_stats.json"))
        out_summary_path = Path(io_config.get("out_summary_path") or (Path(io_config.get("out_root", ".")) / "readers_summary.json"))

        doc_meta_payload = {"documents": [item["doc_meta"] for item in payload["items"]]}
        with io_op("write"):
            save_readers_doc_meta(doc_meta_payload, out_doc_path)
        with io_op("write"):
            save_readers_stage_stats(payload["stage_stats"], out_stats_path)
        with io_op("write"):
            save_readers_summary(payload["summary"], out_summary_path)

        payload["io"] = {
            "out_doc_path": str(out_doc_path),
            "out_stats_path": str(out_stats_path),
            "out_summary_path": str(out_summary_path),
        }

    def _stamp_version(self, result: Dict[str, Any]) -> None:
        result.update(make_artifact_stamp(schema_name="phase_02_readers_output"))


def run_readers(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    config_overrides: Dict[str, Any] | None = None,
    run_id: str | None = None,
    stage_name: str = PHASE_NAME_DEFAULT,
) -> Dict[str, Any]:
    runner = ReadersRunner(PhaseSpec(phase_id=PHASE_ID, name=stage_name))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)
    payload = result.get("payload", {})
    final: Dict[str, Any] = {
        "config": result["config"],
        "items": payload.get("items"),
        "stage_stats": payload.get("stage_stats"),
        "summary": payload.get("summary"),
        "io": payload.get("io"),
    }
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    if "versioning" in result:
        final["versioning"] = result["versioning"]
    return final


__all__ = ["ReadersRunner", "run_readers", "PHASE_ID", "PHASE_NAME_DEFAULT"]
