#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path so 'core' package is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _read_version_file() -> str:
    p = Path("core/versioning/VERSION")
    if not p.exists():
        print("ERROR: VERSION file missing at core/versioning/VERSION", file=sys.stderr)
        sys.exit(2)
    return p.read_text(encoding="utf-8").strip()


def _check_pyproject() -> None:
    pp = Path("pyproject.toml")
    if not pp.exists():
        # Optional: do not fail if pyproject is absent
        return
    try:
        import tomllib  # Python 3.11+
    except Exception:
        print("WARN: tomllib unavailable; skipping pyproject check", file=sys.stderr)
        return
    try:
        data = tomllib.loads(pp.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN: failed to parse pyproject.toml: {exc}", file=sys.stderr)
        return
    ver = data.get("project", {}).get("version")
    if not (isinstance(ver, dict) and ver.get("file") == "core/versioning/VERSION"):
        print("ERROR: pyproject.toml does not point project.version to core/versioning/VERSION", file=sys.stderr)
        sys.exit(3)


def main() -> None:
    from core.versioning import get_version_info

    file_version = _read_version_file()
    _check_pyproject()
    info = get_version_info()
    runtime_version = str(info.get("version"))
    if runtime_version != file_version:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "version-mismatch",
                    "file": file_version,
                    "runtime": runtime_version,
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    print(json.dumps({"ok": True, "version": file_version}))


if __name__ == "__main__":
    main()
