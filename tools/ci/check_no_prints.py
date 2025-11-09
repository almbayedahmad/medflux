#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Iterable


def iter_py_files(root: Path, include: Iterable[str]) -> Iterable[Path]:
    for inc in include:
        base = root / inc
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            yield p


def is_allowed(path: Path) -> bool:
    # Allow prints in tests and developer tools; enforce in runtime code only
    s = str(path).replace("\\", "/")
    return any([
        "/tests/" in s,
        s.startswith("tools/"),
    ])


def has_print_call(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "print":
                return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Disallow stray print() calls in runtime code")
    ap.add_argument("--roots", nargs="*", default=["backend", "core"])
    args = ap.parse_args()
    offender = False
    for p in iter_py_files(Path("."), args.roots):
        if is_allowed(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if has_print_call(text):
            print(f"print() found in runtime code: {p}", file=sys.stderr)
            offender = True
    if offender:
        sys.exit(1)


if __name__ == "__main__":
    main()
