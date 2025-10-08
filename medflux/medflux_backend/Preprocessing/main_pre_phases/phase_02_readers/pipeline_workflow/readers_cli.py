from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from ..connecters.readers_connector_config import connect_readers_config_connector
from ..connecters.readers_connector_metadata import compute_readers_run_metadata
from .readers_pipeline import run_readers_pipeline


_DEF_PIPELINE_ID = "preprocessing.run_readers"
_BASE_CONFIG = connect_readers_config_connector()
_BASE_OPTIONS = dict(_BASE_CONFIG.get("options") or {})
_BASE_IO = dict(_BASE_CONFIG.get("io") or {})


def get_readers_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser("run_readers", description="FluxAI Readers - unified runner")
    parser.add_argument("inputs", nargs="*")
    parser.add_argument("--input", dest="input_flags", action="append", default=[])
    parser.add_argument("--out", "--outdir", dest="outdir", required=True)
    parser.add_argument("--mode", "--mode-default", dest="mode_default", default=_BASE_OPTIONS.get("mode", "mixed"))
    parser.add_argument("--lang", "--lang-default", dest="lang_default", default=_BASE_OPTIONS.get("lang", "deu+eng"))
    parser.add_argument("--dpi", "--dpi-default", dest="dpi_default", type=int, default=int(_BASE_OPTIONS.get("dpi", 300)))
    parser.add_argument("--psm", "--psm-default", dest="psm_default", type=int, default=int(_BASE_OPTIONS.get("psm", 6)))
    parser.add_argument("--blocks-threshold", type=int, default=int(_BASE_OPTIONS.get("blocks_threshold", 3)))
    parser.add_argument("--oem", type=int, default=int(_BASE_OPTIONS.get("oem", 3)))
    parser.add_argument("--workers", type=int, default=int(_BASE_OPTIONS.get("workers", 4)))
    parser.add_argument("--pre", action="store_true", default=bool(_BASE_OPTIONS.get("use_pre", False)))
    parser.add_argument("--export-xlsx", action="store_true", default=bool(_BASE_OPTIONS.get("export_xlsx", False)))
    parser.add_argument("--verbose", action="store_true", default=bool(_BASE_OPTIONS.get("verbose", False)))
    parser.add_argument("--tables", "--tables-default", dest="tables_default", default=_BASE_OPTIONS.get("tables_mode", "detect"))
    parser.add_argument("--save-table-crops", action="store_true", default=bool(_BASE_OPTIONS.get("save_table_crops", False)))
    parser.add_argument("--tables-min-words", type=int, default=int(_BASE_OPTIONS.get("tables_min_words", 12)))
    parser.add_argument("--table-detect-min-area", type=float, default=float(_BASE_OPTIONS.get("table_detect_min_area", 9000.0)))
    parser.add_argument("--table-detect-max-cells", type=int, default=int(_BASE_OPTIONS.get("table_detect_max_cells", 600)))
    parser.add_argument("--native-ocr-overlay", action="store_true", default=bool(_BASE_OPTIONS.get("native_ocr_overlay", False)))
    parser.add_argument("--overlay-area-thr", type=float, default=float(_BASE_OPTIONS.get("overlay_area_thr", 0.35)))
    parser.add_argument("--overlay-min-images", type=int, default=int(_BASE_OPTIONS.get("overlay_min_images", 1)))
    parser.add_argument("--overlay-if-any-image", action="store_true", default=bool(_BASE_OPTIONS.get("overlay_if_any_image", False)))
    return parser.parse_args()


def get_readers_cli_overrides(args: argparse.Namespace) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {
        "io": {
            "out_root": str(Path(args.outdir)),
            "out_doc_path": _BASE_IO.get("out_doc_path"),
            "out_stats_path": _BASE_IO.get("out_stats_path"),
            "out_summary_path": _BASE_IO.get("out_summary_path"),
        },
        "options": {
            "mode": args.mode_default,
            "lang": args.lang_default,
            "dpi": args.dpi_default,
            "psm": args.psm_default,
            "blocks_threshold": args.blocks_threshold,
            "tables_mode": args.tables_default,
            "oem": args.oem,
            "workers": args.workers,
            "use_pre": bool(args.pre),
            "export_xlsx": bool(args.export_xlsx),
            "verbose": bool(args.verbose),
            "save_table_crops": bool(args.save_table_crops),
            "tables_min_words": args.tables_min_words,
            "table_detect_min_area": args.table_detect_min_area,
            "table_detect_max_cells": args.table_detect_max_cells,
            "native_ocr_overlay": bool(args.native_ocr_overlay),
            "overlay_area_thr": args.overlay_area_thr,
            "overlay_min_images": args.overlay_min_images,
            "overlay_if_any_image": bool(args.overlay_if_any_image),
        },
    }
    return overrides


def get_readers_cli_items(args: argparse.Namespace) -> List[Dict[str, Any]]:
    inputs = list(args.inputs) + list(args.input_flags or [])
    if not inputs:
        raise SystemExit("No input files provided. Use positional arguments or --input flags.")
    return [{"path": str(Path(raw_input))} for raw_input in inputs]


def run_readers_cli() -> None:
    args = get_readers_cli_arguments()
    overrides = get_readers_cli_overrides(args)
    items = get_readers_cli_items(args)
    run_meta = compute_readers_run_metadata(pipeline_id=_DEF_PIPELINE_ID)
    payload = run_readers_pipeline(
        items,
        config_overrides=overrides,
        run_metadata=run_meta,
    )
    print(
        json.dumps(
            {
                "outdir": overrides["io"]["out_root"],
                "run_id": run_meta["run_id"],
                "pipeline_id": run_meta["pipeline_id"],
                "count": len(payload["items"]),
            }
        )
    )


if __name__ == "__main__":
    run_readers_cli()
