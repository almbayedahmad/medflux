#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parents[2] / "core" / "versioning" / "VERSION"


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[.-].+)?$")


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def write_version(v: str) -> None:
    VERSION_FILE.write_text(v + "\n", encoding="utf-8")


def bump(v: str, kind: str) -> str:
    m = SEMVER_RE.match(v)
    if not m:
        raise SystemExit(f"Invalid version format: {v}")
    major, minor, patch = map(int, m.groups())
    if kind == "major":
        return f"{major+1}.0.0"
    if kind == "minor":
        return f"{major}.{minor+1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch+1}"
    raise SystemExit(f"Unknown bump kind: {kind}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Bump core version")
    ap.add_argument("kind", choices=["major", "minor", "patch"], help="version part to bump")
    args = ap.parse_args()
    cur = read_version()
    new = bump(cur, args.kind)
    write_version(new)
    print(new)


if __name__ == "__main__":
    main()
