from __future__ import annotations

"""Core processing entry point for the detect_type stage."""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from ..internal_helpers.detect_type_detection_helper import process_detect_type_many
from ..schemas.detect_type_types import FileTypeResult, summarize_detect_type_results, summarize_detect_type_stats


@dataclass
class DetectionInputs:
    """Structured view over the generic stage inputs."""

    valid_paths: List[str]
    skipped_items: List[Dict[str, Any]]
    received_count: int


def _extract_detect_type_paths(items: Sequence[Dict[str, Any]]) -> DetectionInputs:
    valid_paths: List[str] = []
    skipped_items: List[Dict[str, Any]] = []
    for index, item in enumerate(items):
        path = item.get("path") or item.get("file_path") or item.get("source_path")
        if not path:
            skipped_items.append({"index": index, "reason": "missing_path"})
            continue
        valid_paths.append(path)
    return DetectionInputs(valid_paths=valid_paths, skipped_items=skipped_items, received_count=len(items))


def process_detect_type_classifier(
    generic_items: Sequence[Dict[str, Any]] | None,
    detection_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run the file type detection for the provided items.

    Returns a dictionary with the unified_document and stage_stats entries expected by the
    stage contract. Consumers can persist those payloads via the outputs layer.
    """

    items = list(generic_items or [])
    overrides = dict(detection_overrides or {})

    inputs = _extract_detect_type_paths(items)
    results = process_detect_type_many(inputs.valid_paths, **overrides)

    unified_document = summarize_detect_type_results(results)
    unified_document["source"] = {
        "items_received": inputs.received_count,
        "items_included": len(inputs.valid_paths),
    }
    if inputs.skipped_items:
        unified_document["errors"] = inputs.skipped_items

    stage_stats = summarize_detect_type_stats(results)
    stage_stats.update(
        {
            "items_received": inputs.received_count,
            "items_included": len(inputs.valid_paths),
            "items_skipped": len(inputs.skipped_items),
        }
    )

    return {
        "unified_document": unified_document,
        "stage_stats": stage_stats,
        "results": results,
    }
