from __future__ import annotations

import json
from pathlib import Path
from typing import List

from jsonschema import Draft202012Validator


def _metaschema() -> dict:
    return Draft202012Validator.META_SCHEMA


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    root = Path("core/validation/contracts")
    metaschema = _metaschema()
    meta_validator = Draft202012Validator(metaschema)
    failures: List[str] = []
    for p in root.rglob("*.json"):
        try:
            sch = _load_json(p)
            errs = list(meta_validator.iter_errors(sch))
            if errs:
                failures.append(f"{p}: {len(errs)} error(s) vs metaschema")
            else:
                # Ensure the schema compiles in our environment
                Draft202012Validator(sch)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{p}: {exc}")

    if failures:
        for f in failures:
            print(f)
        raise SystemExit(1)
    print("OK: all schemas valid and compilable")


if __name__ == "__main__":
    main()
