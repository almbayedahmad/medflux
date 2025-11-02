from __future__ import annotations

from backend.Preprocessing.main_pre_phases.phase_01_encoding.connecters.encoding_connector_config import (
    connect_encoding_config_connector,
)


def test_encoding_config_contains_outputs() -> None:
    cfg = connect_encoding_config_connector()
    assert cfg.get("stage") == "encoding"
    assert cfg["io"]["out_doc_path"].endswith("encoding_unified_document.json")
    assert cfg["io"]["out_stats_path"].endswith("encoding_stage_stats.json")
