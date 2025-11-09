# PURPOSE:
#   Domain processing entry point for phase_01_encoding (v2 layout).
#   Contains core detection and normalization logic for the encoding stage.
#
# OUTCOME:
#   Provides stable, fully-typed processing functions used by the phase API.
#   No legacy references; aligned with v2 domain helpers.
#
# INPUTS:
#   - generic_items: Sequence[dict] with file paths and optional normalization flags.
#   - detection_cfg: Mapping with detection parameters (sample_bytes, minimum_confidence).
#   - normalization_cfg: Mapping with normalization parameters (enabled, out_dir, errors, newline_policy).
#
# OUTPUTS:
#   - Dict with unified_document, stage_stats, and items lists matching schema helpers.
#
# DEPENDENCIES:
#   - domain helpers: `.helpers.get_encoding_detection_for_path`,
#     `.helpers.normalize_encoding_file_to_utf8`.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .helpers import (
    normalize_encoding_file_to_utf8,
    get_encoding_detection_for_path,
)
from ..schemas.encoding_types import EncodingItem, summarize_encoding_document, summarize_encoding_stats
from core.monitoring import record_doc_processed


@dataclass
class EncodingInput:
    """Prepared input for encoding processing.

    Args:
        path: Absolute or relative file path to process.
        normalize: Whether to emit a normalized UTF-8 copy.
        dest_path: Optional explicit output path for normalized file.
    Outcome:
        Normalizes and validates raw user items before processing.
    """

    path: str
    normalize: bool
    dest_path: Optional[str]


@dataclass
class EncodingInputs:
    """Container for prepared and skipped inputs.

    Args:
        prepared: Successfully prepared inputs to process.
        skipped: Items skipped with reasons (index, reason).
        received_count: Original number of received items.
    Outcome:
        Clear accounting for processing decisions and traceability.
    """

    prepared: List[EncodingInput]
    skipped: List[Dict[str, Any]]
    received_count: int


def process_encoding_prepare_inputs(
    items: Sequence[Dict[str, Any]],
    normalization_cfg: Dict[str, Any],
) -> EncodingInputs:
    """Prepare inputs for the encoding stage.

    Args:
        items: Incoming raw item mappings which may include 'path', 'file_path',
            'normalize', and 'dest_path'.
        normalization_cfg: Normalization config; may include 'enabled' and 'out_dir'.
    Returns:
        EncodingInputs with prepared items and skipped entries with reasons.
    Outcome:
        Produces a deterministic, validated set of inputs for processing logic.
    """

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
    """Run detection and optional normalization for provided items.

    Args:
        generic_items: Sequence of input mappings; see prepare_inputs for keys.
        detection_cfg: Optional detection parameters including 'sample_bytes' and
            'minimum_confidence'.
        normalization_cfg: Optional normalization parameters including 'enabled',
            'out_dir', 'newline_policy', and 'errors'.
    Returns:
        Mapping with keys 'unified_document', 'stage_stats', and 'items'.
    Outcome:
        Stable, validated outputs with deterministic ordering for the pipeline.
    """

    items = list(generic_items or [])
    detection_cfg = dict(detection_cfg or {})
    normalization_cfg = dict(normalization_cfg or {})

    inputs = process_encoding_prepare_inputs(items, normalization_cfg)
    sample_bytes = int(detection_cfg.get("sample_bytes", 1024 * 1024))
    min_conf = float(detection_cfg.get("minimum_confidence", 0.0) or 0.0)

    newline_policy = normalization_cfg.get("newline_policy", "lf")
    errors_policy = normalization_cfg.get("errors", "strict")

    encoding_items: List[EncodingItem] = []
    normalized_count = 0

    for enc_input in inputs.prepared:
        detection = get_encoding_detection_for_path(enc_input.path, sample_bytes=sample_bytes)
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
            outcome = normalize_encoding_file_to_utf8(
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
        # Metrics: document processed and bytes (best-effort, no PII)
        try:
            from pathlib import Path as _P

            ext = _P(enc_input.path).suffix.lower().lstrip(".") or "unknown"
            size = None
            try:
                size = _P(enc_input.path).stat().st_size
            except Exception:
                size = None
            record_doc_processed("phase_01_encoding", ext, bytes_count=size)
            if normalization_payload and normalization_payload.get("ok") and normalization_payload.get("normalized_path"):
                np = str(normalization_payload.get("normalized_path"))
                try:
                    nsize = _P(np).stat().st_size
                except Exception:
                    nsize = None
                record_doc_processed("phase_01_encoding", "normalized", bytes_count=nsize)
        except Exception:
            # Do not let metrics issues break processing
            pass
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


__all__ = [
    "process_encoding_stage",
    "process_encoding_prepare_inputs",
    "EncodingInput",
    "EncodingInputs",
]
