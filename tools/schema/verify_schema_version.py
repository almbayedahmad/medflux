#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _parse_stage_contract_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    # naive parse: look for a line like 'stage_contract: "1.0.0"' or 'stage_contract: 1.0.0'
    m = re.search(r"stage_contract:\s*\"?([0-9]+\.[0-9]+\.[0-9]+)\"?", text)
    return m.group(1) if m else None


def main() -> None:
    schemas_path = Path("core/versioning/schemas.yaml")
    if not schemas_path.exists():
        print("ERROR: schemas.yaml missing at core/versioning/schemas.yaml", file=sys.stderr)
        sys.exit(2)
    declared = _parse_stage_contract_version(schemas_path)
    if not declared:
        print("ERROR: could not read stage_contract version from schemas.yaml", file=sys.stderr)
        sys.exit(3)
    # best-effort import without requiring PyYAML
    try:
        from core.versioning.schemas import get_schema_version  # type: ignore

        runtime = get_schema_version("stage_contract", kind="contracts")
    except Exception:
        runtime = None

    if runtime and str(runtime) != str(declared):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "schema-version-mismatch",
                    "declared": declared,
                    "runtime": runtime,
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps({"ok": True, "stage_contract": declared}))


if __name__ == "__main__":
    main()
