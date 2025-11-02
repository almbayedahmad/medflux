from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from core.logging import configure_logging, get_logger
from core.validation import discover_phase, load_schema, validate_input, validate_output
from core.validation.errors import ValidationError


def _read_any(path: Path, *, jsonl: bool = False) -> Any:
    if jsonl or path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Fallback JSON
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a JSON artifact against a phase schema")
    parser.add_argument("phase", help="Phase name, e.g., phase_00_detect_type")
    parser.add_argument("kind", choices=["input", "output"], help="Which schema to validate against")
    parser.add_argument("file", help="Path or glob to file(s) to validate")
    parser.add_argument("--soft", action="store_true", help="Soft-fail: log warnings instead of raising")
    parser.add_argument("--schema-root", help="Override schema root directory")
    parser.add_argument("--log-json", action="store_true")
    parser.add_argument("--log-level", default=os.environ.get("MEDFLUX_LOG_LEVEL", "INFO"))
    parser.add_argument("--jsonl", action="store_true", help="Treat inputs as JSONL records")
    parser.add_argument("--explain", action="store_true", help="Print top validation errors and exit with code 1 instead of raising")
    parser.add_argument("--out-json", help="Write a JSON report to this path")
    args = parser.parse_args()

    if args.log_json:
        os.environ["MEDFLUX_LOG_FORMAT"] = "json"
    os.environ["MEDFLUX_LOG_LEVEL"] = args.log_level
    configure_logging(force=True)
    log = get_logger("medflux.validation.cli")

    if args.schema_root:
        os.environ["MFLUX_SCHEMA_ROOT"] = args.schema_root

    phase = args.phase
    kind = args.kind
    matched = list(Path().glob(args.file)) if any(c in args.file for c in "*?[") else [Path(args.file)]
    results = []
    for fpath in matched:
        payload = _read_any(fpath, jsonl=args.jsonl)
        try:
            if kind == "input":
                validate_input(phase, payload, soft=args.soft)
            else:
                validate_output(phase, payload, soft=args.soft)
            log.info("Validation OK", extra={"phase": phase, "kind": kind, "path": str(fpath), "code": "VL-I000"})
            results.append({"path": str(fpath), "ok": True})
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", "VL-E000")
            log.error("Validation failed", extra={"phase": phase, "kind": kind, "path": str(fpath), "code": code, "err": str(exc)})
            results.append({"path": str(fpath), "ok": False, "error": str(exc), "code": code})
            if args.explain and isinstance(exc, ValidationError):
                details = exc.details or {}
                errs = details.get("errors") if isinstance(details, dict) else None
                if isinstance(errs, list):
                    print("Top errors:")
                    for i, e in enumerate(errs[:5], 1):
                        print(f"  {i}. {e.get('message')} @ path={e.get('path')} schema_path={e.get('schema_path')}")
                raise SystemExit(1)
            raise
    if args.out_json:
        Path(args.out_json).write_text(json.dumps({"phase": phase, "kind": kind, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
