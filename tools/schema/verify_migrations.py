#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> None:
    mig_dir = Path("core/versioning/migrations")
    mig_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in mig_dir.glob("[0-9][0-9][0-9]_*.yaml"))
    seen = set()
    last_n = 0
    for name in files:
        m = re.match(r"^(\d{3})_", name)
        if not m:
            print(f"Invalid migration filename: {name}", file=sys.stderr)
            sys.exit(2)
        n = int(m.group(1))
        if n in seen:
            print(f"Duplicate migration number: {n}", file=sys.stderr)
            sys.exit(3)
        if n <= last_n:
            print(f"Migration numbering not strictly increasing: {last_n} -> {n}", file=sys.stderr)
            sys.exit(4)
        seen.add(n)
        last_n = n
    print(json.dumps({"ok": True, "count": len(files)}))


if __name__ == "__main__":
    main()
