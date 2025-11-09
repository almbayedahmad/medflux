# PURPOSE:
#   Phase 00 (detect_type) public API and PhaseRunner implementation. Wraps
#   existing connectors and classifier logic into a standardized lifecycle.
#
# OUTCOME:
#   Consistent execution for detect_type while preserving the legacy pipeline
#   function signature and behavior externally.

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from core.preprocessing.config.registry import (
    get_phase_config,
    merge_overrides,
    register_phase_config,
)
from core.preprocessing.phase_api import PhaseRunner, PhaseSpec
from core.preprocessing.metrics import io_op
from core.versioning import make_artifact_stamp

from .connectors.config import connect_detect_type_config_connector
from .connectors.upstream import connect_detect_type_upstream_connector
from .domain.process import process_detect_type_classifier
from .io.writer import save_detect_type_doc, save_detect_type_stats


PHASE_ID = "phase_00_detect_type"
PHASE_NAME_DEFAULT = "detect_type"


def _registry_loader(_profile: Optional[str]) -> Dict[str, Any]:
    return connect_detect_type_config_connector(PHASE_NAME_DEFAULT)


try:
    register_phase_config(PHASE_ID, _registry_loader)
except Exception:
    pass


class DetectTypeRunner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    """Standardized runner for detect_type phase."""

    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = get_phase_config(self.spec.phase_id) or connect_detect_type_config_connector(self.spec.name)
        return merge_overrides(cfg, overrides)

    def _connect_upstream(self, items: Optional[Sequence[Dict[str, Any]]] = None) -> Sequence[Dict[str, Any]]:
        return connect_detect_type_upstream_connector(items)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        payload = process_detect_type_classifier(
            upstream,
            detection_overrides=config.get("detection"),
        )
        return payload

    def _save_outputs(self, payload: Dict[str, Any], *, config: Dict[str, Any]) -> None:
        try:
            with io_op("write"):
                save_detect_type_doc(payload["unified_document"], config)
        except Exception:
            raise
        try:
            with io_op("write"):
                save_detect_type_stats(payload["stage_stats"], config)
        except Exception:
            raise

    def _stamp_version(self, result: Dict[str, Any]) -> None:
        result.update(make_artifact_stamp(schema_name="phase_00_detect_type_output"))


def run_detect_type(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    config_overrides: Dict[str, Any] | None = None,
    run_id: str | None = None,
    stage_name: str = PHASE_NAME_DEFAULT,
) -> Dict[str, Any]:
    runner = DetectTypeRunner(PhaseSpec(phase_id=PHASE_ID, name=stage_name))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)
    payload = result.get("payload", {})
    final: Dict[str, Any] = {"config": result["config"], **payload}
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    if "versioning" in result:
        final["versioning"] = result["versioning"]
    return final


__all__ = ["DetectTypeRunner", "run_detect_type", "PHASE_ID", "PHASE_NAME_DEFAULT"]
