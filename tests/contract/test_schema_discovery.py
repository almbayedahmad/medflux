import pytest
from pathlib import Path
from jsonschema import Draft202012Validator

from core.validation.registry import get_schema_root


pytestmark = pytest.mark.contract


def test_all_stage_schemas_are_valid():
    root = get_schema_root() / "stages"
    assert root.exists(), f"Schema stages root not found: {root}"
    for phase_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for name in ("input.schema.json", "output.schema.json"):
            sp = phase_dir / name
            assert sp.exists(), f"Missing schema file: {sp}"
            data = sp.read_text(encoding="utf-8")
            # Load as JSON via Draft202012Validator.check_schema expects dict; use json module
            import json

            obj = json.loads(data)
            Draft202012Validator.check_schema(obj)
            assert "$id" in obj and isinstance(obj["$id"], str)
