from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .detect_type_pipeline import run_detect_type_pipeline


def _build_items(paths: list[str]) -> list[Dict[str, Any]]:
    return [{"path": path} for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run File Type Detection stage")
    parser.add_argument("paths", nargs="+", help="File paths to classify")
    parser.add_argument("--stage", default="detect_type", help="Stage name override")
    args = parser.parse_args()

    items = _build_items(list(args.paths))
    payload = run_detect_type_pipeline(items, stage_name=args.stage)

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
    main()
