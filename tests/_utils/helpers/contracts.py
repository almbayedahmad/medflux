from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from jsonschema import Draft202012Validator
from core.validation.registry import get_schema_root


def get_schema_path(phase: str, io: str) -> Path:
    io_norm = io.strip().lower()
    if io_norm not in {"input", "output"}:
        raise ValueError("io must be 'input' or 'output'")
    return get_schema_root() / "stages" / phase / f"{io_norm}.schema.json"


def load_schema(phase: str, io: str) -> Dict[str, Any]:
    path = get_schema_path(phase, io)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_json(payload: Any, schema: Dict[str, Any]) -> None:
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def _parse_stage(stage: str) -> Tuple[str, str]:
    """Return (phase, kind) from a stage label like 'phase_01_encoding.output'."""
    parts = stage.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return stage, "unknown"


def _expected_stage_name(phase: str) -> str:
    # Derive expected 'stage' value from phase id suffix
    if phase.startswith("phase_"):
        return phase.split("_", 2)[-1]
    return phase


def cross_field_checks(payload: Dict[str, Any], stage: str) -> None:
    """Lightweight cross-field consistency checks.

    - For all: run_id (if present) is non-empty.
    - For output payloads: stage names and counts are coherent when fields are present.
    """
    if not isinstance(payload, dict):
        return

    phase, kind = _parse_stage(stage)

    # Basic run_id sanity
    run_id = payload.get("run_id")
    if run_id is not None and (not isinstance(run_id, str) or not run_id.strip()):
        raise AssertionError(f"{stage}: run_id must be a non-empty string when present")

    # Only apply the following to outputs
    if kind != "output":
        return

    expected_stage = _expected_stage_name(phase)

    # versioning presence (shape is enforced by schema, presence checked here for clarity)
    if "versioning" in payload and isinstance(payload["versioning"], dict):
        v = payload["versioning"]
        if "app_version" not in v:
            raise AssertionError(f"{stage}: versioning.app_version must be present")

    # unified_document stage name
    ud = payload.get("unified_document")
    if isinstance(ud, dict):
        if "stage" in ud and ud.get("stage") != expected_stage:
            raise AssertionError(
                f"{stage}: unified_document.stage={ud.get('stage')} != expected {expected_stage}"
            )
        items = ud.get("items") if isinstance(ud.get("items"), list) else None
        src = ud.get("source") if isinstance(ud.get("source"), dict) else None
        if isinstance(items, list) and isinstance(src, dict):
            inc = src.get("items_included")
            if isinstance(inc, int) and inc != len(items):
                raise AssertionError(
                    f"{stage}: source.items_included={inc} must equal len(unified_document.items)={len(items)}"
                )

    # stage_stats coherence
    stats = payload.get("stage_stats")
    if isinstance(stats, dict):
        # stage field equals expected when present
        stg = stats.get("stage")
        if isinstance(stg, str) and stg != expected_stage:
            raise AssertionError(f"{stage}: stage_stats.stage={stg} != expected {expected_stage}")
        # total_items vs unified_document.items length when available
        total = stats.get("total_items")
        if isinstance(total, int) and isinstance(ud, dict) and isinstance(ud.get("items"), list):
            if total != len(ud["items"]):
                raise AssertionError(
                    f"{stage}: stage_stats.total_items={total} must equal len(unified_document.items)={len(ud['items'])}"
                )
        # readers phase: documents should match number of items when present
        docs = stats.get("documents")
        if isinstance(docs, int) and isinstance(payload.get("items"), list):
            if docs != len(payload["items"]):
                raise AssertionError(
                    f"{stage}: stage_stats.documents={docs} must equal len(items)={len(payload['items'])}"
                )
