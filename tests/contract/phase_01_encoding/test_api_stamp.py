# PURPOSE:
#   Contract test ensuring encoding API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

from pathlib import Path

import pytest

from backend.Preprocessing.phase_01_encoding.api import run_encoding


pytestmark = pytest.mark.contract


def test_encoding_api_top_level_versioning_stamp(tmp_path: Path) -> None:
    overrides = {
        "io": {
            "out_doc_path": str(tmp_path / "ud.json"),
            "out_stats_path": str(tmp_path / "stats.json"),
        }
    }
    result = run_encoding([], config_overrides=overrides)
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_01_encoding_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
