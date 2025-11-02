#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


def find_latest_log(root: Path, run_id: str | None, phase: str | None) -> Path | None:
    if run_id and phase:
        # assume layout: root/YYYY-MM-DD/run_id/phase.jsonl
        days = sorted([p for p in root.iterdir() if p.is_dir()], reverse=True)
        for day in days:
            candidate = day / run_id / f"{phase}.jsonl"
            if candidate.exists():
                return candidate
        return None
    # fallback: find most recent jsonl
    jsonls = list(root.rglob("*.jsonl"))
    if not jsonls:
        return None
    return max(jsonls, key=lambda p: p.stat().st_mtime)


def tail(path: Path) -> None:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.3)
                continue
            sys.stdout.write(line)
            sys.stdout.flush()


def main() -> None:
    ap = argparse.ArgumentParser(description="Tail MedFlux JSONL logs")
    ap.add_argument("--root", default="logs")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--phase", default=None)
    args = ap.parse_args()
    path = find_latest_log(Path(args.root), args.run_id, args.phase)
    if not path:
        print("No log file found", file=sys.stderr)
        sys.exit(2)
    print(f"Tailing {path}")
    tail(path)


if __name__ == "__main__":
    main()
