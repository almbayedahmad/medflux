from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Optional, Tuple

from jsonschema import Draft202012Validator, ValidationError as JSValidationError
from jsonschema.validators import RefResolver
from functools import lru_cache
from pathlib import Path as _Path

from .errors import ValidationError
from .loader import load_schema
from .registry import discover_phase, get_schema_root
from .formats import format_checker
from .policy import demotion_rules, should_demote
from core.monitoring import validation_span, record_validator_request, record_validator_compile
import time


def _iter_errors(validator: Draft202012Validator, payload: Any) -> Iterable[JSValidationError]:
    return validator.iter_errors(payload)


def _summarize_errors(errors: Iterable[JSValidationError]) -> Tuple[str, list[dict]]:
    details: list[dict] = []
    for e in errors:
        path = list(e.path)
        schema_path = list(e.schema_path)
        details.append({
            "message": e.message,
            "path": path,
            "schema_path": schema_path,
            "validator": e.validator,
        })
    msg = f"{len(details)} validation error(s)"
    return msg, details


def _build_store(root: _Path) -> dict[str, dict]:
    store: dict[str, dict] = {}
    for p in root.rglob("*.json"):
        try:
            sch = load_schema(p)
            uri = p.resolve().as_uri()
            store[uri] = sch
            sid = sch.get("$id") if isinstance(sch, dict) else None
            if isinstance(sid, str) and sid:
                store[sid] = sch
        except Exception:
            continue
    return store


@lru_cache(maxsize=128)
def _compile(schema_path_str: str, mtime: float) -> Draft202012Validator:
    schema_path = _Path(schema_path_str)
    sch = load_schema(schema_path)
    try:
        base_uri = schema_path.resolve().as_uri()
    except Exception:
        base_uri = None
    store = _build_store(get_schema_root())
    resolver = RefResolver(base_uri=base_uri, referrer=sch, store=store) if base_uri else None
    validator = Draft202012Validator(sch, resolver=resolver, format_checker=format_checker)
    # Best-effort: derive phase/kind labels from path to record compiles (cache miss)
    try:
        parts = [p for p in schema_path.parts if p]
        kind = "input" if schema_path.name.startswith("input") else ("output" if schema_path.name.startswith("output") else "unknown")
        phase = "unknown"
        if "stages" in parts:
            idx = parts.index("stages")
            if idx + 1 < len(parts):
                phase = parts[idx + 1]
        record_validator_compile(kind, phase)
    except Exception:
        pass
    return validator


def _env_true(*names: str) -> bool:
    for n in names:
        v = os.environ.get(n, "")
        if isinstance(v, str) and v.strip().lower() in {"1", "true", "yes"}:
            return True
    return False


def validate_input(phase: str, payload: Any, *, soft: bool | None = None) -> None:
    """Validate input payload for a phase.

    soft=True downgrades failures to a logged warning (VL-W001) instead of raising.
    """
    # Record validator request for cache hit/miss accounting
    try:
        record_validator_request("input", phase)
    except Exception:
        pass
    with validation_span("input", phase) as v:
        t0 = time.perf_counter()
        paths = discover_phase(phase, root=get_schema_root())
        sp = paths["input"].resolve()
        validator = _compile(str(sp), sp.stat().st_mtime)
        errors = list(_iter_errors(validator, payload))
        _ = (time.perf_counter() - t0)  # keep for parity, timing handled by validation_span
        if errors:
            if _env_true("MEDFLUX_VALIDATION_DRYRUN", "MFLUX_VALIDATION_DRYRUN"):
                _, details = _summarize_errors(errors)
                logging.getLogger("medflux.validation").warning(
                    "Input validation dry-run", extra={"code": "VL-W001", "phase": phase, "errors": details}
                )
                v["ok"] = True
                return
            rules = demotion_rules()
            demoted = [e for e in errors if should_demote(e, rules)]
            remaining = [e for e in errors if e not in demoted]
            if soft or (demoted and not remaining):
                _, details = _summarize_errors(errors)
                logging.getLogger("medflux.validation").warning(
                    "Input validation soft-fail", extra={"code": "VL-W001", "phase": phase, "errors": details}
                )
                v["ok"] = True
                return
            msg, details = _summarize_errors(remaining)
            v["ok"] = False
            v["code"] = "VL-E001"
            raise ValidationError(msg, code="VL-E001", details={"phase": phase, "errors": details})
        v["ok"] = True


def validate_output(phase: str, payload: Any, *, soft: bool | None = None) -> None:
    """Validate output payload for a phase.

    soft=True downgrades failures to a logged warning (VL-W002) instead of raising.
    """
    try:
        record_validator_request("output", phase)
    except Exception:
        pass
    with validation_span("output", phase) as v:
        t0 = time.perf_counter()
        paths = discover_phase(phase, root=get_schema_root())
        sp = paths["output"].resolve()
        validator = _compile(str(sp), sp.stat().st_mtime)
        errors = list(_iter_errors(validator, payload))
        _ = (time.perf_counter() - t0)
        if errors:
            if _env_true("MEDFLUX_VALIDATION_DRYRUN", "MFLUX_VALIDATION_DRYRUN"):
                _, details = _summarize_errors(errors)
                logging.getLogger("medflux.validation").warning(
                    "Output validation dry-run",
                    extra={"code": "VL-W002", "phase": phase, "errors": details},
                )
                v["ok"] = True
                return
            rules = demotion_rules()
            demoted = [e for e in errors if should_demote(e, rules)]
            remaining = [e for e in errors if e not in demoted]
            if soft or (demoted and not remaining):
                _, details = _summarize_errors(errors)
                logging.getLogger("medflux.validation").warning(
                    "Output validation soft-fail",
                    extra={"code": "VL-W002", "phase": phase, "errors": details},
                )
                v["ok"] = True
                return
            msg, details = _summarize_errors(remaining)
            v["ok"] = False
            v["code"] = "VL-E002"
            raise ValidationError(msg, code="VL-E002", details={"phase": phase, "errors": details})

        # Post-schema cross-field checks
        try:
            if phase == "phase_00_detect_type":
                ud = payload.get("unified_document") if isinstance(payload, dict) else None
                ss = payload.get("stage_stats") if isinstance(payload, dict) else None
                if isinstance(ud, dict) and isinstance(ss, dict):
                    items_len = len(ud.get("items") or [])
                    total_items = ss.get("total_items")
                    if isinstance(total_items, int) and total_items != items_len:
                        raise ValidationError(
                            f"total_items {total_items} != len(items) {items_len}",
                            code="VL-E010",
                            details={
                                "phase": phase,
                                "errors": [
                                    {
                                        "path": ["stage_stats", "total_items"],
                                        "message": "mismatch with unified_document.items",
                                    }
                                ],
                            },
                        )
            elif phase == "phase_01_encoding":
                ud = payload.get("unified_document") if isinstance(payload, dict) else None
                ss = payload.get("stage_stats") if isinstance(payload, dict) else None
                if isinstance(ud, dict) and isinstance(ss, dict):
                    items_len = len(ud.get("items") or [])
                    total_items = ss.get("total_items")
                    if isinstance(total_items, int) and total_items != items_len:
                        raise ValidationError(
                            f"total_items {total_items} != len(items) {items_len}",
                            code="VL-E010",
                            details={
                                "phase": phase,
                                "errors": [
                                    {
                                        "path": ["stage_stats", "total_items"],
                                        "message": "mismatch with unified_document.items",
                                    }
                                ],
                            },
                        )
            elif phase == "phase_02_readers":
                items = payload.get("items") if isinstance(payload, dict) else None
                ss = payload.get("stage_stats") if isinstance(payload, dict) else None
                if isinstance(items, list) and isinstance(ss, dict):
                    count = len(items)
                    items_processed = ss.get("items_processed")
                    if isinstance(items_processed, int) and items_processed != count:
                        raise ValidationError(
                            f"items_processed {items_processed} != len(items) {count}",
                            code="VL-E010",
                            details={
                                "phase": phase,
                                "errors": [
                                    {
                                        "path": ["stage_stats", "items_processed"],
                                        "message": "mismatch with items length",
                                    }
                                ],
                            },
                        )
        except ValidationError as exc:
            if soft or _env_true("MEDFLUX_VALIDATION_DRYRUN", "MFLUX_VALIDATION_DRYRUN"):
                logging.getLogger("medflux.validation").warning(
                    "Output cross-field validation soft-fail",
                    extra={
                        "code": "VL-W010",
                        "phase": phase,
                        "errors": exc.details.get("errors") if isinstance(exc.details, dict) else exc.details,
                    },
                )
                v["ok"] = True
                return
            v["ok"] = False
            v["code"] = exc.code if hasattr(exc, "code") else "VL-E010"
            raise
        v["ok"] = True
