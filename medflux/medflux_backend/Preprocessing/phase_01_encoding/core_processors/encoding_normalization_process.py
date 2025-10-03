from __future__ import annotations

"""Core processing entry point for the encoding stage."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..internal_helpers.encoding_detection_helper import (
    convert_file_to_utf8,
    detect_encoding_for_path,
)
from ..schemas.encoding_types import EncodingItem, summarize_encoding_document, summarize_encoding_stats


@dataclass
class EncodingInput:
    path: str
    normalize: bool
    dest_path: Optional[str]


@dataclass
class EncodingInputs:
    prepared: List[EncodingInput]
    skipped: List[Dict[str, Any]]
    received_count: int


def _extract_inputs(
    items: Sequence[Dict[str, Any]],
    normalization_cfg: Dict[str, Any],
) -> EncodingInputs:
    prepared: List[EncodingInput] = []
    skipped: List[Dict[str, Any]] = []
    default_normalize = bool(normalization_cfg.get("enabled"))
    default_out_dir = normalization_cfg.get("out_dir")

    for index, item in enumerate(items):
        path = item.get("path") or item.get("file_path")
        if not path:
            skipped.append({"index": index, "reason": "missing_path"})
            continue
        normalize = item.get("normalize")
        if normalize is None:
            normalize = default_normalize
        normalize = bool(normalize)
        dest_path = item.get("dest_path")
        if dest_path is None and default_out_dir:
            src = Path(path)
            suffix = src.suffix or ".txt"
            stem = src.stem or src.name
            dest_path = str(Path(default_out_dir) / f"{stem}.utf8{suffix}")
        prepared.append(EncodingInput(path=str(path), normalize=normalize, dest_path=dest_path))
    return EncodingInputs(prepared=prepared, skipped=skipped, received_count=len(items))


def process_encoding_stage(
    generic_items: Sequence[Dict[str, Any]] | None,
    detection_cfg: Dict[str, Any] | None = None,
    normalization_cfg: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    items = list(generic_items or [])
    detection_cfg = dict(detection_cfg or {})
    normalization_cfg = dict(normalization_cfg or {})

    inputs = _extract_inputs(items, normalization_cfg)
    sample_bytes = int(detection_cfg.get("sample_bytes", 1024 * 1024))
    min_conf = float(detection_cfg.get("minimum_confidence", 0.0) or 0.0)

    newline_policy = normalization_cfg.get("newline_policy", "lf")
    errors_policy = normalization_cfg.get("errors", "strict")

    encoding_items: List[EncodingItem] = []
    normalized_count = 0

    for enc_input in inputs.prepared:
        detection = detect_encoding_for_path(enc_input.path, sample_bytes=sample_bytes)
        detection_payload = {
            "encoding": detection.encoding,
            "confidence": detection.confidence,
            "bom": detection.bom,
            "is_utf8": detection.is_utf8,
            "sample_len": detection.sample_len,
        }
        if detection_payload["confidence"] is not None and min_conf > 0:
            detection_payload["low_confidence"] = detection_payload["confidence"] < min_conf

        normalization_payload: Optional[Dict[str, Any]] = None
        if enc_input.normalize:
            dest_path = enc_input.dest_path
            outcome = convert_file_to_utf8(
                enc_input.path,
                detection=detection,
                dest_path=dest_path,
                newline_policy=newline_policy,
                errors=errors_policy,
            )
            normalization_payload = {
                "ok": outcome.ok,
                "normalized_path": outcome.normalized_path,
                "reason": outcome.reason,
            }
            if outcome.ok:
                normalized_count += 1
        encoding_items.append(
            EncodingItem(
                file_path=enc_input.path,
                detection=detection_payload,
                normalization=normalization_payload,
            )
        )

    unified_document = summarize_encoding_document(encoding_items)
    unified_document["source"] = {
        "items_received": inputs.received_count,
        "items_included": len(inputs.prepared),
    }
    if inputs.skipped:
        unified_document["errors"] = inputs.skipped

    stage_stats = summarize_encoding_stats(encoding_items)
    stage_stats.update(
        {
            "items_received": inputs.received_count,
            "items_included": len(inputs.prepared),
            "items_skipped": len(inputs.skipped),
            "normalized_success": normalized_count,
        }
    )

    return {
        "unified_document": unified_document,
        "stage_stats": stage_stats,
        "items": encoding_items,
    }
