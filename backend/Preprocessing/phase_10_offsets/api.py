# PURPOSE:
#   Phase 10 (offsets) public API and PhaseRunner implementation (v2 scaffold).
# OUTCOME:
#   Standardized lifecycle with a minimal implementation.

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from core.preprocessing.phase_api import PhaseRunner, PhaseSpec
from core.versioning import make_artifact_stamp
from core.preprocessing.config.registry import merge_overrides

from .connectors.config import connect_offsets_config_connector
from .connectors.upstream import connect_offsets_upstream_connector
from .domain.process import process_offsets_items


PHASE_ID = "phase_10_offsets"
PHASE_NAME_DEFAULT = "offsets"


class OffsetsRunner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return merge_overrides(connect_offsets_config_connector(PHASE_NAME_DEFAULT), overrides)

    def _connect_upstream(self, items: Optional[Sequence[Dict[str, Any]]] = None) -> Sequence[Dict[str, Any]]:
        return connect_offsets_upstream_connector(items)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        return process_offsets_items(list(upstream))

    def _stamp_version(self, result: Dict[str, Any]) -> None:
        result.update(make_artifact_stamp(schema_name="phase_10_offsets_output"))


def run_offsets(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    config_overrides: Dict[str, Any] | None = None,
    run_id: str | None = None,
    stage_name: str = PHASE_NAME_DEFAULT,
) -> Dict[str, Any]:
    """Run the offsets phase using the standardized runner.

    Args:
        generic_items: Optional list of input items for the phase.
        config_overrides: Optional configuration overrides.
        run_id: Optional run identifier to stamp into outputs.
        stage_name: Stage name (defaults to "offsets").
    Returns:
        Mapping of config plus payload keys.
    Outcome:
        Stable public API surface for invoking the offsets phase.
    """
    runner = OffsetsRunner(PhaseSpec(phase_id=PHASE_ID, name=stage_name))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)
    payload = result.get("payload", {})
    final: Dict[str, Any] = {"config": result["config"], **payload}
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    return final


__all__ = ["OffsetsRunner", "run_offsets", "PHASE_ID", "PHASE_NAME_DEFAULT"]
