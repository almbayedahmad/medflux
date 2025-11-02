from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List, Optional

from jsonschema import Draft202012Validator
from jsonschema.validators import RefResolver


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _store_for(root: Path) -> dict[str, dict]:
    store: dict[str, dict] = {}
    for sp in root.rglob("*.json"):
        try:
            sch = _load_json(sp)
            store[sp.resolve().as_uri()] = sch
            sid = sch.get("$id") if isinstance(sch, dict) else None
            if isinstance(sid, str) and sid:
                store[sid] = sch
        except Exception:
            continue
    return store


def _artifact_schema_for(path: Path) -> Optional[Path]:
    name = path.name.lower()
    base = Path("core/validation/contracts/artifacts")
    mapping = {
        "detect_type_unified_document.json": base / "detect_type" / "unified_document.schema.json",
        "detect_type_stage_stats.json": base / "detect_type" / "stage_stats.schema.json",
        "encoding_unified_document.json": base / "encoding" / "unified_document.schema.json",
        "encoding_stage_stats.json": base / "encoding" / "stage_stats.schema.json",
        "readers_doc_meta.json": base / "readers" / "doc_meta.schema.json",
        "readers_stage_stats.json": base / "readers" / "stage_stats.schema.json",
        "readers_summary.json": base / "readers" / "summary.schema.json",
    }
    return mapping.get(name)


def _base_contract_schema() -> dict:
    # Minimal schema: require versioning.app_version
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["versioning"],
        "properties": {
            "versioning": {
                "type": "object",
                "required": ["app_version"],
                "properties": {"app_version": {"type": "string"}},
            }
        },
        "additionalProperties": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate saved artifact JSONs against artifact schemas (or versioning fallback)")
    parser.add_argument("paths", nargs="+", help="Artifact JSON paths to validate")
    parser.add_argument("--auto", action="store_true", help="Auto-select artifact schema based on filename")
    parser.add_argument("--out-json", help="Write a JSON report to this path")
    args = parser.parse_args()

    root = Path("core/validation/contracts")
    store = _store_for(root)

    failures: List[str] = []
    results: List[dict] = []
    for raw in args.paths:
        p = Path(raw)
        try:
            payload = _load_json(p)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{p}: {exc}")
            results.append({"path": str(p), "ok": False, "error": str(exc)})
            continue

        sch_path = _artifact_schema_for(p) if args.auto else None
        if sch_path and sch_path.exists():
            sch = _load_json(sch_path)
            resolver = RefResolver(base_uri=sch_path.resolve().as_uri(), referrer=sch, store=store)
            validator = Draft202012Validator(sch, resolver=resolver)
        else:
            validator = Draft202012Validator(_base_contract_schema())

        errors = list(validator.iter_errors(payload))
        if errors:
            failures.append(f"{p}: {len(errors)} error(s)")
            results.append({"path": str(p), "ok": False, "errors": len(errors)})
        else:
            results.append({"path": str(p), "ok": True})

    if args.out_json:
        report = {"checked": len(results), "failed": sum(1 for r in results if not r.get("ok")), "results": results}
        Path(args.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        for f in failures:
            print(f)
        raise SystemExit(1)
    print("OK: artifacts validated")


if __name__ == "__main__":
    main()
