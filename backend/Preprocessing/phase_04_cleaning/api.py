# PURPOSE:
#   Phase 04 (cleaning) public API and PhaseRunner implementation (v2 scaffold).
# OUTCOME:
#   Standardized lifecycle with a minimal implementation.

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from core.preprocessing.phase_api import PhaseRunner, PhaseSpec
from core.preprocessing.metrics import io_op
from core.versioning import make_artifact_stamp
from core.preprocessing.config.registry import merge_overrides

from .connectors.config import connect_cleaning_config_connector
from .connectors.upstream import connect_cleaning_upstream_connector
from .domain.process import process_cleaning_items
from .io.writer import save_cleaning_doc, save_cleaning_stats


PHASE_ID = "phase_04_cleaning"
PHASE_NAME_DEFAULT = "cleaning"


class CleaningRunner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return merge_overrides(connect_cleaning_config_connector(PHASE_NAME_DEFAULT), overrides)

    def _connect_upstream(self, items: Optional[Sequence[Dict[str, Any]]] = None) -> Sequence[Dict[str, Any]]:
        return connect_cleaning_upstream_connector(items)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        return process_cleaning_items(list(upstream))

    def _save_outputs(self, payload: Dict[str, Any], *, config: Dict[str, Any]) -> None:
        try:
            with io_op("write"):
                save_cleaning_doc(payload.get("unified_document", {}), config)
        except Exception:
            raise
        try:
            with io_op("write"):
                save_cleaning_stats(payload.get("stage_stats", {}), config)
        except Exception:
            raise

    def _stamp_version(self, result: Dict[str, Any]) -> None:
        result.update(make_artifact_stamp(schema_name="phase_04_cleaning_output"))


def run_cleaning(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    config_overrides: Dict[str, Any] | None = None,
    run_id: str | None = None,
    stage_name: str = PHASE_NAME_DEFAULT,
) -> Dict[str, Any]:
    """Run the cleaning phase using the standardized runner.

    Args:
        generic_items: Optional list of input items for the phase.
        config_overrides: Optional configuration overrides.
        run_id: Optional run identifier to stamp into outputs.
        stage_name: Stage name (defaults to "cleaning").
    Returns:
        Mapping of config plus payload keys.
    Outcome:
        Stable public API surface for invoking the cleaning phase.
    """
    runner = CleaningRunner(PhaseSpec(phase_id=PHASE_ID, name=stage_name))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)
    payload = result.get("payload", {})
    final: Dict[str, Any] = {"config": result["config"], **payload}
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    return final


__all__ = ["CleaningRunner", "run_cleaning", "PHASE_ID", "PHASE_NAME_DEFAULT"]
