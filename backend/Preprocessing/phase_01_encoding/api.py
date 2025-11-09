# PURPOSE:
#   Phase 01 (encoding) public API and PhaseRunner implementation.
#   This wraps existing connectors and domain logic into a standardized
#   lifecycle while preserving the classic pipeline entry points.
#
# OUTCOME:
#   Consistent, testable execution path for the encoding phase with stable
#   interfaces. External imports can continue using the legacy pipeline module.

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

# Local imports from legacy modules (kept intact)
from .connectors.config import connect_encoding_config_connector
from .connectors.upstream import connect_encoding_upstream_connector
from .domain.process import process_encoding_stage
from .io.writer import save_encoding_doc, save_encoding_stats


PHASE_ID = "phase_01_encoding"
PHASE_NAME_DEFAULT = "encoding"


def _registry_loader(_profile: Optional[str]) -> Dict[str, Any]:  # profile unused for now
    return connect_encoding_config_connector(PHASE_NAME_DEFAULT)


# Register the phase config loader once on import.
try:
    register_phase_config(PHASE_ID, _registry_loader)
except Exception:
    pass


class EncodingRunner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    """Standardized runner for the encoding phase."""

    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = get_phase_config(self.spec.phase_id) or connect_encoding_config_connector(self.spec.name)
        return merge_overrides(cfg, overrides)

    def _connect_upstream(self, items: Optional[Sequence[Dict[str, Any]]] = None) -> Sequence[Dict[str, Any]]:
        return connect_encoding_upstream_connector(items)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        payload = process_encoding_stage(
            upstream,
            detection_cfg=config.get("detection"),
            normalization_cfg=config.get("normalization"),
        )
        # Add a generated_at timestamp if not present
        import time

        stage_stats = payload.get("stage_stats") or {}
        stage_stats.setdefault("generated_at_ms", int(time.time() * 1000))
        return payload

    def _save_outputs(self, payload: Dict[str, Any], *, config: Dict[str, Any]) -> None:
        try:
            with io_op("write"):
                save_encoding_doc(payload["unified_document"], config)
        except Exception:
            # Let caller surface the IO error like the legacy pipeline
            raise
        try:
            with io_op("write"):
                save_encoding_stats(payload["stage_stats"], config)
        except Exception:
            raise

    def _stamp_version(self, result: Dict[str, Any]) -> None:
        result.update(make_artifact_stamp(schema_name="phase_01_encoding_output"))


def run_encoding(
    generic_items: Sequence[Dict[str, Any]] | None = None,
    *,
    config_overrides: Dict[str, Any] | None = None,
    run_id: str | None = None,
    stage_name: str = PHASE_NAME_DEFAULT,
) -> Dict[str, Any]:
    """Run the encoding phase using the standardized runner.

    Returns a mapping compatible with the legacy pipeline result structure:
    {"config": cfg, **payload, "versioning": {...}, (optional) "run_id": run_id}
    """

    runner = EncodingRunner(PhaseSpec(phase_id=PHASE_ID, name=stage_name))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)

    payload = result.get("payload", {})
    final: Dict[str, Any] = {"config": result["config"], **payload}
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    if "versioning" in result:
        final["versioning"] = result["versioning"]
    return final


__all__ = ["EncodingRunner", "run_encoding", "PHASE_ID", "PHASE_NAME_DEFAULT"]
