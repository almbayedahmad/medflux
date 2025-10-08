from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .encoding_pipeline import run_encoding_pipeline


def process_encoding_build_items(paths: list[str], normalize: bool) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    for path in paths:
        entry: Dict[str, Any] = {"path": path}
        if normalize:
            entry["normalize"] = True
        items.append(entry)
    return items


def run_encoding_cli() -> None:
    parser = argparse.ArgumentParser(description="Run Encoding stage")
    parser.add_argument("paths", nargs="+", help="Input files to analyse")
    parser.add_argument("--stage", default="encoding", help="Stage name override")
    parser.add_argument("--normalize", action="store_true", help="Enable UTF-8 normalization")
    parser.add_argument("--dest-outdir", help="Destination directory for normalized files")
    parser.add_argument("--newline", choices=["lf", "crlf"], help="Newline normalization policy")
    parser.add_argument("--errors", choices=["strict", "replace", "ignore"], help="Decoding error policy")
    args = parser.parse_args()

    items = process_encoding_build_items(list(args.paths), args.normalize)

    overrides: Dict[str, Any] = {}
    normalization_cfg: Dict[str, Any] = {}
    if args.normalize:
        normalization_cfg["enabled"] = True
    if args.dest_outdir:
        normalization_cfg["out_dir"] = args.dest_outdir
    if args.newline:
        normalization_cfg["newline_policy"] = args.newline
    if args.errors:
        normalization_cfg["errors"] = args.errors
    if normalization_cfg:
        overrides["normalization"] = normalization_cfg

    payload = run_encoding_pipeline(
        items,
        stage_name=args.stage,
        config_overrides=overrides or None,
    )

    print(
        json.dumps(
            {
                "unified_document": payload["unified_document"],
                "stage_stats": payload["stage_stats"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    run_encoding_cli()
