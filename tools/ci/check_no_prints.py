#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


ALLOW_SUBSTRINGS = (
    "if __name__ == '__main__':",
)


def iter_py_files(root: Path, include: Iterable[str]) -> Iterable[Path]:
    for inc in include:
        base = root / inc
        for p in base.rglob("*.py"):
            yield p


def is_allowed(path: Path) -> bool:
    # Allow prints in CLIs, tests, and tools scripts
    parts = [str(path)]
    s = str(path).replace("\\", "/")
    return any(
        [
            s.endswith("_cli.py"),
            "/tests/" in s,
            s.startswith("tools/"),
        ]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Disallow stray print() calls in runtime code")
    ap.add_argument("--roots", nargs="*", default=["backend", "core"])
    args = ap.parse_args()
    offender = False
    pat = re.compile(r"\bprint\s*\(")
    for p in iter_py_files(Path("."), args.roots):
        if is_allowed(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if pat.search(text):
            print(f"print() found in runtime code: {p}", file=sys.stderr)
            offender = True
    if offender:
        sys.exit(1)


if __name__ == "__main__":
    main()
