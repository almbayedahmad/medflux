#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Create/update a 'latest' pointer for a run's log file")
    ap.add_argument("log_file", help="Path to a JSONL log file")
    ap.add_argument("--root", default="logs")
    args = ap.parse_args()
    root = Path(args.root)
    target = Path(args.log_file).resolve()
    latest_dir = root / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    # Try symlink; fall back to copy of path text
    link = latest_dir / target.name
    try:
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(str(target), str(link))
        print(f"Symlinked {link} -> {target}")
    except Exception:
        # Fallback: write a pointer file
        ptr = latest_dir / (target.stem + ".path.txt")
        ptr.write_text(str(target), encoding="utf-8")
        # Optionally copy file
        shutil.copy2(str(target), str(latest_dir / target.name))
        print(f"Wrote pointer {ptr} and copied log file")


if __name__ == "__main__":
    main()
