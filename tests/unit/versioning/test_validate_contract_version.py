from __future__ import annotations

import json
from pathlib import Path

from core.versioning.schemas import validate_contract_version


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_validate_contract_version_ok():
    doc = _load_json(Path("outputs/detect_type_unified_document.json"))
    ok, msg = validate_contract_version("stage_contract", doc)
    assert ok is True
    assert msg in {"ok", "no-expected-version"} or "ok" in msg


def test_validate_contract_version_mismatch():
    doc = _load_json(Path("outputs/detect_type_unified_document.json"))
    # Tamper with version
    doc["versioning"]["schema_version"] = "9.9.9"
    ok, msg = validate_contract_version("stage_contract", doc)
    assert ok is False
    assert "mismatch" in msg or "missing" in msg

