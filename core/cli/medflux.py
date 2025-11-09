# PURPOSE:
#   Umbrella CLI for MedFlux phases and chains.
#
# OUTCOME:
#   Provides a single entrypoint `medflux` to run individual phases (detect,
#   encoding, readers) and the preprocessing chain with consistent arguments.
#
# INPUTS:
#   - Subcommands and arguments parsed via argparse.
#
# OUTPUTS:
#   - Prints JSON-like summaries to stdout; phases persist outputs when their
#     APIs are called with default IO overrides.
#
# DEPENDENCIES:
#   - Uses phase APIs under `backend.Preprocessing.phase_XX_*` and the
#     `core.preprocessing.pipeline.preprocessing_chain` integration.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _coerce_inputs(values: List[str]) -> List[str]:
    paths: List[str] = []
    for raw in values:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"input not found: {p}")
        paths.append(str(p))
    return paths


def _print(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_phase_list(_args: argparse.Namespace) -> None:
    root = Path("backend/Preprocessing").resolve()
    phases: List[str] = []
    if root.exists():
        for child in root.iterdir():
            if child.is_dir() and child.name.startswith("phase_") and (child / "api.py").exists():
                phases.append(child.name)
    _print({"phases": sorted(phases)})


def cmd_phase_run_detect(args: argparse.Namespace) -> None:
    from backend.Preprocessing.phase_00_detect_type.api import run_detect_type

    items = [{"path": p} for p in _coerce_inputs(args.inputs)]
    overrides: Dict[str, Any] = {}
    if args.output_root:
        out_dir = Path(args.output_root).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        overrides["io"] = {
            "out_doc_path": str(out_dir / "detect_type_unified_document.json"),
            "out_stats_path": str(out_dir / "detect_type_stage_stats.json"),
        }
    payload = run_detect_type(items, config_overrides=overrides or None, run_id=args.run_id)
    _print({"phase": "phase_00_detect_type", "run_id": payload.get("run_id"), "io": payload.get("io"), "versioning": payload.get("versioning")})


def cmd_phase_run_encoding(args: argparse.Namespace) -> None:
    from backend.Preprocessing.phase_01_encoding.api import run_encoding

    items = [{"path": p, "normalize": bool(args.normalize)} for p in _coerce_inputs(args.inputs)]
    overrides: Dict[str, Any] = {}
    if args.output_root:
        out_dir = Path(args.output_root).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        overrides["io"] = {
            "out_doc_path": str(out_dir / "encoding_unified_document.json"),
            "out_stats_path": str(out_dir / "encoding_stage_stats.json"),
        }
        if args.normalize:
            overrides["normalization"] = {"enabled": True, "out_dir": str(out_dir / "normalized"), "newline_policy": "lf", "errors": "replace"}
    payload = run_encoding(items, config_overrides=overrides or None, run_id=args.run_id)
    _print({"phase": "phase_01_encoding", "run_id": payload.get("run_id"), "io": payload.get("io"), "versioning": payload.get("versioning")})


def cmd_phase_run_readers(args: argparse.Namespace) -> None:
    from backend.Preprocessing.phase_02_readers.api import run_readers

    items = [{"path": p} for p in _coerce_inputs(args.inputs)]
    overrides: Dict[str, Any] = {}
    if args.output_root:
        out_dir = Path(args.output_root).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        overrides["io"] = {"out_doc_path": str(out_dir / "readers_doc_meta.json"), "out_stats_path": str(out_dir / "readers_stage_stats.json"), "out_summary_path": str(out_dir / "readers_summary.json")}
    payload = run_readers(items, config_overrides=overrides or None, run_id=args.run_id)
    _print({"phase": "phase_02_readers", "run_id": payload.get("run_id"), "io": payload.get("io"), "versioning": payload.get("versioning")})


def cmd_chain_run(args: argparse.Namespace) -> None:
    from core.preprocessing.pipeline.preprocessing_chain import run_preprocessing_chain

    inputs = _coerce_inputs(args.inputs)
    summary = run_preprocessing_chain(
        inputs,
        output_root=args.output_root,
        run_id=args.run_id,
        normalize=bool(args.normalize),
        include_docs=bool(args.include_docs),
        include_merge=bool(getattr(args, "include_merge", False)),
        include_cleaning=bool(getattr(args, "include_cleaning", False)),
    )
    _print(summary)


def build_parser() -> argparse.ArgumentParser:
    """Build the umbrella CLI argument parser.

    Outcome:
        Exposes subcommands for all preprocessing phases and the chain runner,
        with consistent logging flags handled centrally.
    """
    parser = argparse.ArgumentParser(prog="medflux", description="MedFlux umbrella CLI")
    # Global logging flags (honored via central logging policy)
    parser.add_argument("--log-level", default=None, help="Logging level (e.g., INFO, DEBUG)")
    parser.add_argument("--log-json", action="store_true", help="Enable JSON logging format")
    parser.add_argument("--log-stderr", action="store_true", help="Log to stderr (console)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # phase list
    p_list = sub.add_parser("phase-list", help="List available phases")
    p_list.set_defaults(func=cmd_phase_list)

    # phase run detect
    p_detect = sub.add_parser("phase-detect", help="Run phase 00 (detect_type)")
    p_detect.add_argument("--inputs", nargs="+", required=True, help="Input files")
    p_detect.add_argument("--output-root", default=None, help="Optional output root directory")
    p_detect.add_argument("--run-id", default=None, help="Optional run identifier")
    p_detect.set_defaults(func=cmd_phase_run_detect)

    # phase run encoding
    p_encoding = sub.add_parser("phase-encoding", help="Run phase 01 (encoding)")
    p_encoding.add_argument("--inputs", nargs="+", required=True, help="Input files")
    p_encoding.add_argument("--output-root", default=None, help="Optional output root directory")
    p_encoding.add_argument("--run-id", default=None, help="Optional run identifier")
    p_encoding.add_argument("--normalize", action="store_true", help="Enable normalization where applicable")
    p_encoding.set_defaults(func=cmd_phase_run_encoding)

    # phase run readers
    p_readers = sub.add_parser("phase-readers", help="Run phase 02 (readers)")
    p_readers.add_argument("--inputs", nargs="+", required=True, help="Input files")
    p_readers.add_argument("--output-root", default=None, help="Optional output root directory")
    p_readers.add_argument("--run-id", default=None, help="Optional run identifier")
    p_readers.set_defaults(func=cmd_phase_run_readers)

    # chain run
    p_chain = sub.add_parser("chain-run", help="Run chain: detect -> encoding -> readers (-> merge -> cleaning -> light_normalization -> segmentation -> table_extraction -> heavy_normalization -> provenance -> offsets)")
    p_chain.add_argument("--inputs", nargs="+", required=True, help="Input documents")
    p_chain.add_argument("--output-root", default=None, help="Optional output root directory")
    p_chain.add_argument("--run-id", default=None, help="Optional run identifier")
    p_chain.add_argument("--normalize", action="store_true", help="Enable normalization in encoding phase")
    p_chain.add_argument("--include-docs", action="store_true", help="Include documents in returned summary")
    p_chain.add_argument("--include-merge", action="store_true", help="Include phase 03 (merge) after readers")
    p_chain.add_argument("--include-cleaning", action="store_true", help="Include phase 04 (cleaning) after readers or merge")
    p_chain.add_argument("--include-light-normalization", action="store_true", help="Include phase 05 (light_normalization) after cleaning/merge/readers")
    p_chain.add_argument("--include-segmentation", action="store_true", help="Include phase 06 (segmentation) after previous stages")
    p_chain.add_argument("--include-table-extraction", action="store_true", help="Include phase 07 (table_extraction) after previous stages")
    p_chain.add_argument("--include-heavy-normalization", action="store_true", help="Include phase 08 (heavy_normalization) after previous stages")
    p_chain.add_argument("--include-provenance", action="store_true", help="Include phase 09 (provenance) after previous stages")
    p_chain.add_argument("--include-offsets", action="store_true", help="Include phase 10 (offsets) after previous stages")
    p_chain.set_defaults(func=cmd_chain_run)

    # phase 03: merge
    p_merge = sub.add_parser("phase-merge", help="Run phase 03 (merge)")
    p_merge.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_merge.add_argument("--output-root", default=None, help="Optional output root directory")
    p_merge.add_argument("--run-id", default=None, help="Optional run identifier")
    def _merge(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_03_merge.api import run_merge
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_merge(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_03_merge", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_merge.set_defaults(func=_merge)

    # phase 04: cleaning
    p_clean = sub.add_parser("phase-cleaning", help="Run phase 04 (cleaning)")
    p_clean.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_clean.add_argument("--output-root", default=None, help="Optional output root directory")
    p_clean.add_argument("--run-id", default=None, help="Optional run identifier")
    def _clean(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_04_cleaning.api import run_cleaning
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_cleaning(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_04_cleaning", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_clean.set_defaults(func=_clean)

    # phase 05: light_normalization
    p_ln = sub.add_parser("phase-light-normalization", help="Run phase 05 (light_normalization)")
    p_ln.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_ln.add_argument("--output-root", default=None, help="Optional output root directory")
    p_ln.add_argument("--run-id", default=None, help="Optional run identifier")
    def _ln(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_05_light_normalization.api import run_light_normalization
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_light_normalization(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_05_light_normalization", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_ln.set_defaults(func=_ln)

    # phase 06: segmentation
    p_seg = sub.add_parser("phase-segmentation", help="Run phase 06 (segmentation)")
    p_seg.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_seg.add_argument("--output-root", default=None, help="Optional output root directory")
    p_seg.add_argument("--run-id", default=None, help="Optional run identifier")
    def _seg(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_06_segmentation.api import run_segmentation
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_segmentation(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_06_segmentation", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_seg.set_defaults(func=_seg)

    # phase 07: table_extraction
    p_te = sub.add_parser("phase-table-extraction", help="Run phase 07 (table_extraction)")
    p_te.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_te.add_argument("--output-root", default=None, help="Optional output root directory")
    p_te.add_argument("--run-id", default=None, help="Optional run identifier")
    def _te(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_07_table_extraction.api import run_table_extraction
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_table_extraction(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_07_table_extraction", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_te.set_defaults(func=_te)

    # phase 08: heavy_normalization
    p_hn = sub.add_parser("phase-heavy-normalization", help="Run phase 08 (heavy_normalization)")
    p_hn.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_hn.add_argument("--output-root", default=None, help="Optional output root directory")
    p_hn.add_argument("--run-id", default=None, help="Optional run identifier")
    def _hn(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_08_heavy_normalization.api import run_heavy_normalization
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_heavy_normalization(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_08_heavy_normalization", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_hn.set_defaults(func=_hn)

    # phase 09: provenance
    p_prov = sub.add_parser("phase-provenance", help="Run phase 09 (provenance)")
    p_prov.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_prov.add_argument("--output-root", default=None, help="Optional output root directory")
    p_prov.add_argument("--run-id", default=None, help="Optional run identifier")
    def _prov(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_09_provenance.api import run_provenance
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_provenance(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_09_provenance", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_prov.set_defaults(func=_prov)

    # phase 10: offsets
    p_off = sub.add_parser("phase-offsets", help="Run phase 10 (offsets)")
    p_off.add_argument("--inputs", nargs="+", required=True, help="Input items")
    p_off.add_argument("--output-root", default=None, help="Optional output root directory")
    p_off.add_argument("--run-id", default=None, help="Optional run identifier")
    def _off(ns: argparse.Namespace) -> None:
        from backend.Preprocessing.phase_10_offsets.api import run_offsets
        items = [{"path": p} for p in _coerce_inputs(ns.inputs)]
        overrides: Dict[str, Any] = {"io": {"out_root": ns.output_root}} if ns.output_root else {}
        payload = run_offsets(items, config_overrides=overrides or None, run_id=ns.run_id)
        _print({"phase": "phase_10_offsets", "run_id": payload.get("run_id"), "versioning": payload.get("versioning")})
    p_off.set_defaults(func=_off)

    return parser


def main(argv: List[str] | None = None) -> int:
    """Entry point for the `medflux` umbrella CLI.

    Outcome:
        Configures logging from flags/env and dispatches to the selected
        subcommand.
    """
    parser = build_parser()
    ns = parser.parse_args(argv)
    # Apply centralized logging based on profile and flags
    try:
        import os
        from core.logging import configure_logging

        if getattr(ns, "log_level", None):
            os.environ["MEDFLUX_LOG_LEVEL"] = str(ns.log_level)
        if bool(getattr(ns, "log_json", False)):
            os.environ["MEDFLUX_LOG_JSON"] = "1"
        if bool(getattr(ns, "log_stderr", False)):
            os.environ["MEDFLUX_LOG_TO_STDERR"] = "1"
        configure_logging(force=True)
    except Exception:
        # Fallback: ignore logging configuration errors to not block CLI
        pass
    ns.func(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
