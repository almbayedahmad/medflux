# PURPOSE:
#   Contract test ensuring cleaning API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_04_cleaning.api import run_cleaning


pytestmark = pytest.mark.contract


def test_cleaning_api_top_level_versioning_stamp() -> None:
    result = run_cleaning([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_04_cleaning_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
