#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    version_file = Path("core/versioning/VERSION")
    changelog = Path("CHANGELOG.md")
    if not version_file.exists():
        print("ERROR: VERSION file missing at core/versioning/VERSION", file=sys.stderr)
        sys.exit(2)
    v = version_file.read_text(encoding="utf-8").strip()
    if not changelog.exists():
        print("ERROR: CHANGELOG.md missing (required when version changes)", file=sys.stderr)
        sys.exit(3)
    text = changelog.read_text(encoding="utf-8")
    if v not in text:
        print(f"ERROR: CHANGELOG.md does not contain version {v}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: CHANGELOG contains version {v}")


if __name__ == "__main__":
    main()
