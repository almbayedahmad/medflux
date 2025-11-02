#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator


def load_schema(path: Path) -> Dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_file(path: Path, schema: Dict[str, Any], *, require_code_on_levels=("WARNING", "ERROR", "CRITICAL"), min_context_ratio: float = 0.9) -> int:
    validator = Draft202012Validator(schema)
    total = 0
    ok = 0
    ctx_ok = 0
    code_viol = 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # schema
            try:
                validator.validate(obj)
                ok += 1
            except Exception as exc:
                print(f"Schema violation in {path}: {exc}", file=sys.stderr)
            # context ratio
            if obj.get("run_id") and obj.get("phase"):
                ctx_ok += 1
            # code on warn/error
            if str(obj.get("level", "")).upper() in require_code_on_levels and not obj.get("code"):
                code_viol += 1

    if total == 0:
        return 0

    ratio = ctx_ok / float(total)
    rc = 0
    if ratio < min_context_ratio:
        print(f"Context coverage too low in {path}: {ratio:.2%} < {min_context_ratio:.2%}", file=sys.stderr)
        rc = 1
    if code_viol > 0:
        print(f"Found {code_viol} WARN/ERROR without code in {path}", file=sys.stderr)
        rc = 1
    return rc


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate MedFlux JSONL logs against schema and policy")
    ap.add_argument("--root", default="logs")
    ap.add_argument("--glob", default="**/*.jsonl")
    ap.add_argument("--schema", default="core/logging/log_record.schema.json")
    ap.add_argument("--min-context", type=float, default=0.9)
    args = ap.parse_args()
    root = Path(args.root)
    schema = load_schema(Path(args.schema))
    paths = [Path(p) for p in glob.glob(str(root / args.glob), recursive=True)]
    if not paths:
        print("No log files found; skipping", file=sys.stderr)
        return
    rc = 0
    for p in paths:
        rc |= validate_file(p, schema, min_context_ratio=args.min_context)
    if rc != 0:
        sys.exit(rc)


if __name__ == "__main__":
    main()
