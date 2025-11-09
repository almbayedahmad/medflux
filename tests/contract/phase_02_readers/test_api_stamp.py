# PURPOSE:
#   Contract test ensuring readers API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

from pathlib import Path

import pytest

from backend.Preprocessing.phase_02_readers.api import run_readers


pytestmark = pytest.mark.contract


def test_readers_api_top_level_versioning_stamp(tmp_path: Path) -> None:
    overrides = {"io": {"out_root": str(tmp_path)}}
    result = run_readers([], config_overrides=overrides)
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_02_readers_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
