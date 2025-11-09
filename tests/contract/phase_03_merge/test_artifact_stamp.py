# PURPOSE:
#   Contract tests for merge artifacts stamping.
# OUTCOME:
#   Ensures unified_document and stage_stats artifacts include versioning
#   with expected schema name and version.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.Preprocessing.phase_03_merge.io.writer import (
    save_merge_doc,
    save_merge_stats,
)


pytestmark = pytest.mark.contract


def test_merge_writers_stamp_versioning(tmp_path: Path) -> None:
    doc_p = tmp_path / "merge_unified_document.json"
    stats_p = tmp_path / "merge_stage_stats.json"

    cfg = {"io": {"out_doc_path": str(doc_p), "out_stats_path": str(stats_p)}}

    save_merge_doc({"unified_document": {}}, cfg)
    save_merge_stats({"stage_stats": {"processed": 0}}, cfg)

    for p in (doc_p, stats_p):
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "versioning" in data
        v = data["versioning"]
        assert v.get("schema_name") == "phase_03_merge_output"
        assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
