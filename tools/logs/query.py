#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict


def make_predicate(level: str | None, code: str | None, phase: str | None, run_id: str | None) -> Callable[[Dict[str, Any]], bool]:
    def _pred(obj: Dict[str, Any]) -> bool:
        if level and str(obj.get("level", "")).upper() != level.upper():
            return False
        if code and str(obj.get("code")) != code:
            return False
        if phase and str(obj.get("phase")) != phase:
            return False
        if run_id and str(obj.get("run_id")) != run_id:
            return False
        return True

    return _pred


def main() -> None:
    ap = argparse.ArgumentParser(description="Query MedFlux JSONL logs")
    ap.add_argument("path", help="Path to a JSONL log file")
    ap.add_argument("--level", help="Filter by level")
    ap.add_argument("--code", help="Filter by code")
    ap.add_argument("--phase", help="Filter by phase")
    ap.add_argument("--run-id", help="Filter by run_id")
    args = ap.parse_args()
    pred = make_predicate(args.level, args.code, args.phase, args.run_id)

    path = Path(args.path)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if pred(obj):
                print(json.dumps(obj, ensure_ascii=False))


if __name__ == "__main__":
    main()
