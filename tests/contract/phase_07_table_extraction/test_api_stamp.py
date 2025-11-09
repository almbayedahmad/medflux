# PURPOSE:
#   Contract test ensuring table_extraction API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_07_table_extraction.api import run_table_extraction


pytestmark = pytest.mark.contract


def test_table_extraction_api_top_level_versioning_stamp() -> None:
    result = run_table_extraction([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_07_table_extraction_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
