from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator
from jsonschema.validators import RefResolver

from core.validation import validate_input, validate_output
from core.validation.errors import ValidationError


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _expand_phase_pairs(pairs: List[str]) -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    for raw in pairs or []:
        try:
            phase, glob = raw.split(":", 1)
        except ValueError:
            raise SystemExit(f"Invalid phase pair: {raw}. Use PHASE:GLOB")
        for p in Path().glob(glob):
            out.append((phase, p))
    return out


def _scan_logs(root: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for p in root.rglob("*.jsonl"):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            code = obj.get("code") if isinstance(obj, dict) else None
            if isinstance(code, str) and code.startswith("VL-"):
                counts[code] = counts.get(code, 0) + 1
    return counts


def _artifact_schema_map() -> Dict[str, Path]:
    base = Path("core/validation/contracts/artifacts")
    return {
        "detect_type_unified_document.json": base / "detect_type" / "unified_document.schema.json",
        "detect_type_stage_stats.json": base / "detect_type" / "stage_stats.schema.json",
        "encoding_unified_document.json": base / "encoding" / "unified_document.schema.json",
        "encoding_stage_stats.json": base / "encoding" / "stage_stats.schema.json",
        "readers_doc_meta.json": base / "readers" / "doc_meta.schema.json",
        "readers_stage_stats.json": base / "readers" / "stage_stats.schema.json",
        "readers_summary.json": base / "readers" / "summary.schema.json",
    }


def _store_for(root: Path) -> dict:
    store: Dict[str, dict] = {}
    for sp in root.rglob("*.json"):
        try:
            sch = _read_json(sp)
            store[sp.resolve().as_uri()] = sch
            sid = sch.get("$id") if isinstance(sch, dict) else None
            if isinstance(sid, str) and sid:
                store[sid] = sch
        except Exception:
            continue
    return store


def validate_artifacts(paths: List[Path]) -> Dict[str, Any]:
    root = Path("core/validation/contracts")
    store = _store_for(root)
    mapping = _artifact_schema_map()
    results: List[dict] = []
    failures = 0
    for p in paths:
        try:
            payload = _read_json(p)
        except Exception as exc:  # noqa: BLE001
            results.append({"path": str(p), "ok": False, "error": str(exc)})
            failures += 1
            continue
        sch_path = mapping.get(p.name.lower())
        if sch_path and sch_path.exists():
            sch = _read_json(sch_path)
            validator = Draft202012Validator(sch, resolver=RefResolver(base_uri=sch_path.resolve().as_uri(), referrer=sch, store=store))
            errors = list(validator.iter_errors(payload))
            if errors:
                results.append({"path": str(p), "ok": False, "errors": len(errors)})
                failures += 1
            else:
                results.append({"path": str(p), "ok": True})
        else:
            results.append({"path": str(p), "ok": True, "note": "no schema mapping"})
    return {"checked": len(results), "failed": failures, "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a consolidated validation report across phases, logs, and artifacts")
    parser.add_argument("--phase-output", action="append", default=[], help="Pairs PHASE:GLOB for output validation (repeat)")
    parser.add_argument("--phase-input", action="append", default=[], help="Pairs PHASE:GLOB for input validation (repeat)")
    parser.add_argument("--logs-root", default="logs", help="Root of logs to scan for VL-* codes")
    parser.add_argument("--artifact", action="append", default=[], help="Artifact JSON path (repeat)")
    parser.add_argument("--out-json", help="Write JSON report here")
    parser.add_argument("--out-md", help="Write Markdown report here")
    parser.add_argument("--max-fail-rate", type=float, default=1.0, help="Max allowed fail rate (0..1)")
    parser.add_argument("--fail-on-codes", default="", help="Comma-separated VL-* codes that cause failure if found in logs")
    args = parser.parse_args()

    phase_sections: List[dict] = []
    total_checks = 0
    total_fails = 0

    for phase, path in _expand_phase_pairs(args.phase_output):
        try:
            payload = _read_json(path)
        except Exception as exc:  # noqa: BLE001
            phase_sections.append({"phase": phase, "kind": "output", "path": str(path), "ok": False, "error": str(exc)})
            total_checks += 1
            total_fails += 1
            continue
        try:
            validate_output(phase, payload, soft=False)
            phase_sections.append({"phase": phase, "kind": "output", "path": str(path), "ok": True})
        except ValidationError as exc:  # noqa: BLE001
            phase_sections.append({"phase": phase, "kind": "output", "path": str(path), "ok": False, "code": exc.code, "errors": exc.details})
            total_fails += 1
        finally:
            total_checks += 1

    for phase, path in _expand_phase_pairs(args.phase_input):
        try:
            payload = _read_json(path)
        except Exception as exc:  # noqa: BLE001
            phase_sections.append({"phase": phase, "kind": "input", "path": str(path), "ok": False, "error": str(exc)})
            total_checks += 1
            total_fails += 1
            continue
        try:
            validate_input(phase, payload, soft=False)
            phase_sections.append({"phase": phase, "kind": "input", "path": str(path), "ok": True})
        except ValidationError as exc:  # noqa: BLE001
            phase_sections.append({"phase": phase, "kind": "input", "path": str(path), "ok": False, "code": exc.code, "errors": exc.details})
            total_fails += 1
        finally:
            total_checks += 1

    # Logs
    code_counts = _scan_logs(Path(args.logs_root)) if args.logs_root else {}
    fail_on = {c.strip() for c in (args.fail_on_codes or "").split(",") if c.strip()}
    codes_triggered = {k: v for k, v in code_counts.items() if k in fail_on}

    # Artifacts
    artifacts = [Path(p) for p in (args.artifact or []) if p]
    artifacts_report = validate_artifacts(artifacts) if artifacts else {"checked": 0, "failed": 0, "results": []}

    # Summary
    fail_rate = (total_fails / total_checks) if total_checks else 0.0
    summary = {
        "checks": total_checks,
        "failed": total_fails,
        "fail_rate": fail_rate,
        "phases": phase_sections,
        "logs": {"codes": code_counts, "fail_on": list(fail_on), "triggered": codes_triggered},
        "artifacts": artifacts_report,
    }

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_md:
        lines: List[str] = []
        lines.append("# Validation Report")
        lines.append("")
        lines.append(f"- Checks: {total_checks}")
        lines.append(f"- Failed: {total_fails}")
        lines.append(f"- Fail rate: {fail_rate:.3f}")
        lines.append("")
        lines.append("## Logs (VL-* codes)")
        for code, count in sorted(code_counts.items()):
            lines.append(f"- {code}: {count}")
        lines.append("")
        lines.append("## Phase Validations")
        for sec in phase_sections:
            ok = "OK" if sec.get("ok") else "FAIL"
            lines.append(f"- {sec['phase']} {sec['kind']} {ok} - {sec['path']}")
        lines.append("")
        lines.append("## Artifact Validations")
        lines.append(f"- Checked: {artifacts_report['checked']}, Failed: {artifacts_report['failed']}")
        Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

    # Enforce thresholds
    if codes_triggered or (fail_rate > float(args.max_fail_rate)) or (artifacts_report.get("failed") or 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
