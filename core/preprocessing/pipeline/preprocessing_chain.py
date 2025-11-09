from __future__ import annotations

# PURPOSE:
#   Integration harness chaining preprocessing phases (00 detect_type -> 01 encoding -> 02 readers -> (optional) 03 merge).
#
# OUTCOME:
#   Provides a simple programmatic API to run the chain with
#   consistent IO handling and an on-disk summary artifact for smoke runs.

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.preprocessing.output.output_router import OutputRouter
from backend.Preprocessing.phase_00_detect_type.api import (
    run_detect_type,
)
from backend.Preprocessing.phase_01_encoding.api import (
    run_encoding,
)
from core.preprocessing.services.readers import ReadersService
from backend.Preprocessing.phase_02_readers.api import (
    run_readers,
)
from backend.Preprocessing.phase_03_merge.api import (
    run_merge,
)
from core.logging import get_logger

logger = get_logger("cli")


def _resolve_inputs(inputs: Sequence[str]) -> List[str]:
    """Resolve and validate input file paths.

    Args:
        inputs: Raw input paths.
    Returns:
        Absolute, existing paths suitable for downstream phases.
    Outcome:
        Raises if no inputs are provided or a path does not exist.
    """

    resolved: List[str] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"input file not found: {path}")
        resolved.append(str(path))
    if not resolved:
        raise ValueError("No input files provided to preprocessing chain")
    return resolved


def run_preprocessing_chain(
    inputs: Sequence[str],
    *,
    output_root: Path | str | None = None,
    run_id: str | None = None,
    normalize: bool = True,
    include_docs: bool = False,
    include_merge: bool = False,
    include_cleaning: bool = False,
    include_light_normalization: bool = False,
    include_segmentation: bool = False,
    include_table_extraction: bool = False,
    include_heavy_normalization: bool = False,
    include_provenance: bool = False,
    include_offsets: bool = False,
) -> Dict[str, Any]:
    """Execute detect_type -> encoding -> readers (-> merge) for the given inputs.

    Outcome:
        Returns a summary mapping with resolved output paths and optional
        embedded documents; writes a JSON summary under the router root.
    """

    resolved_inputs = _resolve_inputs(inputs)
    root_override: Path | None = None
    if output_root is not None:
        root_path = output_root if isinstance(output_root, Path) else Path(output_root)
        root_override = root_path.expanduser().resolve()
        root_override.mkdir(parents=True, exist_ok=True)

    router = OutputRouter(root=root_override, run_id=run_id)

    # Stage 0: detect_type
    detect_io = router.stage_io("detector")
    detect_overrides: Dict[str, Any] = {
        "io": detect_io.as_overrides(),
    }
    detect_payload = run_detect_type(
        [{"path": path} for path in resolved_inputs],
        config_overrides=detect_overrides,
    )
    detect_items = detect_payload["unified_document"]["items"]
    detect_lookup = {item["file_path"]: item for item in detect_items}

    # Stage 1: encoding
    encoding_items: List[Dict[str, Any]] = []
    for path in resolved_inputs:
        detection = detect_lookup.get(path, {})
        recommended = detection.get("recommended") or {}
        item: Dict[str, Any] = {"path": path}
        if recommended.get("lang"):
            item["lang"] = recommended["lang"]
        if recommended.get("mode"):
            item["mode"] = recommended["mode"]
        file_type = str(detection.get("file_type") or "").lower()
        if normalize and file_type in {"txt", "docx"}:
            item["normalize"] = True
        encoding_items.append(item)

    encoding_io = router.stage_io("encoder")
    encoding_overrides: Dict[str, Any] = {
        "io": encoding_io.as_overrides(),
    }
    if normalize:
        normalization_dir = router.normalization_dir("encoder")
        encoding_overrides["normalization"] = {
            "enabled": True,
            "out_dir": str(normalization_dir),
            "newline_policy": "lf",
            "errors": "strict",
        }
    encoding_payload = run_encoding(
        encoding_items,
        config_overrides=encoding_overrides,
    )

    encoding_docs = encoding_payload["unified_document"]["items"]
    encoding_lookup = {entry["file_path"]: entry for entry in encoding_docs}

    # Stage 2: readers
    readers_items: List[Dict[str, Any]] = []
    normalized_files: List[str] = []
    for path in resolved_inputs:
        enc_entry = encoding_lookup.get(path, {})
        normalization = enc_entry.get("normalization") or {}
        normalized_path = None
        if normalization.get("ok") and normalization.get("normalized_path"):
            normalized_path = normalization["normalized_path"]
            normalized_files.append(normalized_path)
        effective_path = normalized_path or path

        detection = detect_lookup.get(path, {})
        recommended = detection.get("recommended") or {}
        readers_item: Dict[str, Any] = {"path": effective_path}
        mode = recommended.get("mode")
        if mode and mode != "off":
            readers_item["mode"] = mode
        lang = recommended.get("lang")
        if lang:
            readers_item["lang"] = lang
        tables_mode = recommended.get("tables_mode")
        if tables_mode and tables_mode not in {"off", "none"}:
            readers_item["tables_mode"] = tables_mode
        readers_items.append(readers_item)

    readers_io = router.stage_io("readers")
    readers_overrides: Dict[str, Any] = {
        "io": readers_io.as_overrides(),
    }
    readers_run_meta = ReadersService.compute_run_metadata(pipeline_id="preprocessing.chain")
    readers_payload = run_readers(
        readers_items,
        config_overrides=readers_overrides,
        run_metadata=readers_run_meta,
    )

    outputs: Dict[str, Any] = {}
    summary = {
        "generated_at": int(time.time()),
        "inputs": resolved_inputs,
        "outputs": outputs,
        "run_id": router.run_id,
    }

    outputs["detect_type"] = {
        "stage_stats": detect_payload["stage_stats"],
        "doc_path": str(detect_io.doc_path),
        "stats_path": str(detect_io.stats_path),
    }
    if include_docs:
        outputs["detect_type"]["document"] = detect_payload["unified_document"]

    outputs["encoding"] = {
        "stage_stats": encoding_payload["stage_stats"],
        "doc_path": str(encoding_io.doc_path),
        "stats_path": str(encoding_io.stats_path),
        "normalized_files": normalized_files,
    }
    if include_docs:
        outputs["encoding"]["document"] = encoding_payload["unified_document"]

    reader_summary = readers_payload.get("summary", {})
    outputs["readers"] = {
        "stage_stats": readers_payload["stage_stats"],
        "doc_path": str(readers_io.doc_path),
        "stats_path": str(readers_io.stats_path),
        "summary_path": str(readers_io.summary_path) if readers_io.summary_path else None,
        "warnings": reader_summary.get("warnings", []),
    }
    if include_docs:
        outputs["readers"]["document"] = readers_payload.get("items")
        outputs["readers"]["summary"] = reader_summary

    # Optional Stage 3: merge
    if include_merge:
        merge_items = readers_payload.get("items") or []
        merge_io = router.stage_io("merge")
        merge_overrides: Dict[str, Any] = {
            "io": merge_io.as_overrides(),
        }
        merge_payload = run_merge(
            merge_items,
            config_overrides=merge_overrides,
        )
        outputs["merge"] = {
            "stage_stats": merge_payload.get("stage_stats", {}),
            "doc_path": str(merge_io.doc_path),
            "stats_path": str(merge_io.stats_path),
        }
        if include_docs:
            outputs["merge"]["document"] = merge_payload.get("unified_document")

    # Optional Stage 4: cleaning
    if include_cleaning:
        from backend.Preprocessing.phase_04_cleaning.api import run_cleaning

        # Prefer merged document items if available
        cleaning_items = []
        try:
            if include_merge:
                cleaning_items = (merge_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            cleaning_items = []
        if not cleaning_items:
            cleaning_items = readers_payload.get("items") or []

        cleaning_io = router.stage_io("cleaning")
        cleaning_overrides: Dict[str, Any] = {"io": cleaning_io.as_overrides()}
        cleaning_payload = run_cleaning(
            cleaning_items,
            config_overrides=cleaning_overrides,
        )
        outputs["cleaning"] = {
            "stage_stats": cleaning_payload.get("stage_stats", {}),
            "doc_path": str(cleaning_io.doc_path),
            "stats_path": str(cleaning_io.stats_path),
        }
        if include_docs:
            outputs["cleaning"]["document"] = cleaning_payload.get("unified_document")

    # Optional Stage 5: light_normalization
    if include_light_normalization:
        from backend.Preprocessing.phase_05_light_normalization.api import run_light_normalization

        ln_items = []
        try:
            if include_cleaning:
                ln_items = (cleaning_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            ln_items = []
        if not ln_items:
            try:
                if include_merge:
                    ln_items = (merge_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
            except Exception:
                ln_items = []
        if not ln_items:
            ln_items = readers_payload.get("items") or []

        ln_io = router.stage_io("light_normalization")
        ln_overrides: Dict[str, Any] = {"io": ln_io.as_overrides()}
        ln_payload = run_light_normalization(
            ln_items,
            config_overrides=ln_overrides,
        )
        outputs["light_normalization"] = {
            "stage_stats": ln_payload.get("stage_stats", {}),
            "doc_path": str(ln_io.doc_path),
            "stats_path": str(ln_io.stats_path),
        }
        if include_docs:
            outputs["light_normalization"]["document"] = ln_payload.get("unified_document")

    # Optional Stage 6: segmentation
    if include_segmentation:
        from backend.Preprocessing.phase_06_segmentation.api import run_segmentation

        seg_items = []
        try:
            if include_light_normalization:
                seg_items = (ln_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            seg_items = []
        if not seg_items:
            try:
                if include_cleaning:
                    seg_items = (cleaning_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
            except Exception:
                seg_items = []
        if not seg_items:
            seg_items = readers_payload.get("items") or []

        seg_io = router.stage_io("segmentation")
        seg_overrides: Dict[str, Any] = {"io": seg_io.as_overrides()}
        seg_payload = run_segmentation(seg_items, config_overrides=seg_overrides)
        outputs["segmentation"] = {
            "stage_stats": seg_payload.get("stage_stats", {}),
            "doc_path": str(seg_io.doc_path),
            "stats_path": str(seg_io.stats_path),
        }
        if include_docs:
            outputs["segmentation"]["document"] = seg_payload.get("unified_document")

    # Optional Stage 7: table_extraction
    if include_table_extraction:
        from backend.Preprocessing.phase_07_table_extraction.api import run_table_extraction

        te_items = []
        try:
            if include_segmentation:
                te_items = (seg_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            te_items = []
        if not te_items:
            te_items = readers_payload.get("items") or []

        te_io = router.stage_io("table_extraction")
        te_overrides: Dict[str, Any] = {"io": te_io.as_overrides()}
        te_payload = run_table_extraction(te_items, config_overrides=te_overrides)
        outputs["table_extraction"] = {
            "stage_stats": te_payload.get("stage_stats", {}),
            "doc_path": str(te_io.doc_path),
            "stats_path": str(te_io.stats_path),
        }
        if include_docs:
            outputs["table_extraction"]["document"] = te_payload.get("unified_document")

    # Optional Stage 8: heavy_normalization
    if include_heavy_normalization:
        from backend.Preprocessing.phase_08_heavy_normalization.api import run_heavy_normalization

        hn_items = []
        try:
            if include_segmentation:
                hn_items = (seg_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            hn_items = []
        if not hn_items:
            hn_items = readers_payload.get("items") or []

        hn_io = router.stage_io("heavy_normalization")
        hn_overrides: Dict[str, Any] = {"io": hn_io.as_overrides()}
        hn_payload = run_heavy_normalization(hn_items, config_overrides=hn_overrides)
        outputs["heavy_normalization"] = {
            "stage_stats": hn_payload.get("stage_stats", {}),
            "doc_path": str(hn_io.doc_path),
            "stats_path": str(hn_io.stats_path),
        }
        if include_docs:
            outputs["heavy_normalization"]["document"] = hn_payload.get("unified_document")

    # Optional Stage 9: provenance
    if include_provenance:
        from backend.Preprocessing.phase_09_provenance.api import run_provenance

        prov_items = []
        try:
            if include_heavy_normalization:
                prov_items = (hn_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            prov_items = []
        if not prov_items:
            prov_items = readers_payload.get("items") or []

        prov_io = router.stage_io("provenance")
        prov_overrides: Dict[str, Any] = {"io": prov_io.as_overrides()}
        prov_payload = run_provenance(prov_items, config_overrides=prov_overrides)
        outputs["provenance"] = {
            "stage_stats": prov_payload.get("stage_stats", {}),
            "doc_path": str(prov_io.doc_path),
            "stats_path": str(prov_io.stats_path),
        }
        if include_docs:
            outputs["provenance"]["document"] = prov_payload.get("unified_document")

    # Optional Stage 10: offsets
    if include_offsets:
        from backend.Preprocessing.phase_10_offsets.api import run_offsets

        off_items = []
        try:
            if include_heavy_normalization:
                off_items = (hn_payload.get("unified_document") or {}).get("items") or []  # type: ignore[name-defined]
        except Exception:
            off_items = []
        if not off_items:
            off_items = readers_payload.get("items") or []

        off_io = router.stage_io("offsets")
        off_overrides: Dict[str, Any] = {"io": off_io.as_overrides()}
        off_payload = run_offsets(off_items, config_overrides=off_overrides)
        outputs["offsets"] = {
            "stage_stats": off_payload.get("stage_stats", {}),
            "doc_path": str(off_io.doc_path),
            "stats_path": str(off_io.stats_path),
        }
        if include_docs:
            outputs["offsets"]["document"] = off_payload.get("unified_document")

    summary_path = router.chain_summary_path()
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    return summary


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add CLI arguments for the chain runner."""

    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input document paths to process (phase 00 -> phase 02).",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help=(
            "Optional base directory for smoke outputs. "
            "Defaults to MEDFLUX_OUTPUT_ROOT (or <repo>/outputs/preprocessing)."
        ),
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run identifier for folder names (defaults to timestamp).",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip UTF-8 normalization in the encoding stage.",
    )
    parser.add_argument(
        "--include-docs",
        action="store_true",
        help="Embed stage documents and readers summary inside the chain summary JSON.",
    )
    parser.add_argument(
        "--include-merge",
        action="store_true",
        help="Include phase 03 (merge) after readers.",
    )
    parser.add_argument(
        "--include-cleaning",
        action="store_true",
        help="Include phase 04 (cleaning) after readers or merge.",
    )
    parser.add_argument(
        "--include-light-normalization",
        action="store_true",
        help="Include phase 05 (light_normalization) after cleaning/merge/readers.",
    )
    parser.add_argument(
        "--include-segmentation",
        action="store_true",
        help="Include phase 06 (segmentation) after previous stages.",
    )
    parser.add_argument(
        "--include-table-extraction",
        action="store_true",
        help="Include phase 07 (table_extraction) after previous stages.",
    )
    parser.add_argument(
        "--include-heavy-normalization",
        action="store_true",
        help="Include phase 08 (heavy_normalization) after previous stages.",
    )
    parser.add_argument(
        "--include-provenance",
        action="store_true",
        help="Include phase 09 (provenance) after previous stages.",
    )
    parser.add_argument(
        "--include-offsets",
        action="store_true",
        help="Include phase 10 (offsets) after previous stages.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for running the preprocessing chain."""
    parser = argparse.ArgumentParser(
        description="Run detect_type, encoding, and readers stages in sequence.",
    )
    _add_arguments(parser)
    args = parser.parse_args(argv)

    summary = run_preprocessing_chain(
        args.inputs,
        output_root=args.output_root,
        run_id=args.run_id,
        normalize=not args.no_normalize,
        include_docs=args.include_docs,
        include_merge=args.include_merge,
        include_cleaning=args.include_cleaning,
        include_light_normalization=args.include_light_normalization,
        include_segmentation=args.include_segmentation,
        include_table_extraction=args.include_table_extraction,
        include_heavy_normalization=args.include_heavy_normalization,
        include_provenance=args.include_provenance,
        include_offsets=args.include_offsets,
    )
    logger.info(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
