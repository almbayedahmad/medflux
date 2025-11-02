from __future__ import annotations

"""Integration harness chaining phases 00 -> 02."""

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

from backend.Preprocessing.main_pre_output.output_router import OutputRouter
from backend.Preprocessing.main_pre_phases.phase_00_detect_type.pipeline_workflow.detect_type_pipeline import (
    run_detect_type_pipeline,
)
from backend.Preprocessing.main_pre_phases.phase_01_encoding.pipeline_workflow.encoding_pipeline import (
    run_encoding_pipeline,
)
from backend.Preprocessing.main_pre_phases.phase_02_readers.connecters.readers_connector_metadata import (
    compute_readers_run_metadata,
)
from backend.Preprocessing.main_pre_phases.phase_02_readers.pipeline_workflow.readers_pipeline import (
    run_readers_pipeline,
)


def _resolve_inputs(inputs: Sequence[str]) -> List[str]:
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
) -> Dict[str, Any]:
    """Execute detect_type -> encoding -> readers for the given inputs."""

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
    detect_payload = run_detect_type_pipeline(
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
    encoding_payload = run_encoding_pipeline(
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
    readers_run_meta = compute_readers_run_metadata(pipeline_id="preprocessing.chain")
    readers_payload = run_readers_pipeline(
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

    summary_path = router.chain_summary_path()
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    return summary


def _add_arguments(parser: argparse.ArgumentParser) -> None:
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
            "Defaults to main_pre_output/output_pre_smoke_results."
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


def main(argv: Sequence[str] | None = None) -> int:
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
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
