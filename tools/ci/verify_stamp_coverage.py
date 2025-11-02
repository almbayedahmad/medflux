#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    # Verify that stage outputs contain a top-level versioning stamp and basic fields
    outputs_root = Path("outputs")
    if not outputs_root.exists():
        print("WARN: outputs/ not found; skipping stamp coverage check", file=sys.stderr)
        print(json.dumps({"ok": True, "skipped": True}))
        return

    failures = []
    checked = 0
    for p in outputs_root.rglob("*.json"):
        checked += 1
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{p}: {exc}")
            continue
        v = obj.get("versioning") if isinstance(obj, dict) else None
        if not isinstance(v, dict) or not v.get("app_version"):
            failures.append(f"{p}: missing versioning.app_version")

    if failures:
        for f in failures:
            print(f, file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"ok": True, "checked": checked}))


if __name__ == "__main__":
    main()
