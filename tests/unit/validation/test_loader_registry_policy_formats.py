from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from core.validation.loader import load_schema
from core.validation.registry import discover_phase, get_schema_root
from core.validation.policy import demotion_rules, should_demote
from core.validation.formats import _RUN_ID_RE


def test_load_schema_json_and_yaml(tmp_path: Path) -> None:
    j = tmp_path / "s.json"
    y = tmp_path / "s.yaml"
    j.write_text(json.dumps({"a": 1}), encoding="utf-8")
    y.write_text("a: 2\n", encoding="utf-8")
    assert load_schema(j)["a"] == 1
    assert load_schema(y)["a"] == 2


def test_load_schema_unsupported(tmp_path: Path) -> None:
    p = tmp_path / "s.txt"
    p.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        load_schema(p)


def test_registry_get_schema_root_env_absolute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Absolute path override
    absdir = tmp_path / "schemas"
    absdir.mkdir()
    monkeypatch.setenv("MEDFLUX_SCHEMA_ROOT", str(absdir))
    p = get_schema_root()
    assert p == absdir


def test_discover_phase_existing() -> None:
    paths = discover_phase("phase_00_detect_type")
    assert paths["input"].name == "input.schema.json"
    assert paths["output"].name == "output.schema.json"


def test_demotions_and_should_demote() -> None:
    rules = demotion_rules()
    # The sample policy includes additionalProperties and a stage_stats path substring
    class Err:
        def __init__(self, validator: str, schema_path: list[object]):
            self.validator = validator
            self.schema_path = schema_path

    assert should_demote(Err("additionalProperties", []), rules) is True
    # Build a schema_path that yields the exact substring in rules when joined
    assert should_demote(Err("type", ["/properties", "stage_stats", "x"]), rules) is True
    assert should_demote(Err("type", ["properties", "something_else"]), rules) is False


@pytest.mark.parametrize(
    "val,ok",
    [
        ("20250101T120000-deadbeef", True),
        ("2025-01-01T120000-deadbeef", False),
        ("RID-1", False),
    ],
)
def test_run_id_format(val: str, ok: bool) -> None:
    assert bool(_RUN_ID_RE.match(val)) is ok
