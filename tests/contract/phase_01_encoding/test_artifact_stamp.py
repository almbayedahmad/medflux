# PURPOSE:
#   Contract tests for encoding artifacts stamping.
# OUTCOME:
#   Ensures artifacts include versioning with schema name and version.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.Preprocessing.phase_01_encoding.io.writer import (
    save_encoding_doc,
    save_encoding_stats,
)


pytestmark = pytest.mark.contract


def test_encoding_writers_stamp_versioning(tmp_path: Path) -> None:
    doc_path = tmp_path / "encoding_doc.json"
    stats_path = tmp_path / "encoding_stats.json"

    cfg = {"io": {"out_doc_path": str(doc_path), "out_stats_path": str(stats_path)}}

    save_encoding_doc({"unified_document": {}}, cfg)
    save_encoding_stats({"stage_stats": {}}, cfg)

    for p in (doc_path, stats_path):
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "versioning" in data
        v = data["versioning"]
        assert v.get("schema_name") == "phase_01_encoding_output"
        assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
