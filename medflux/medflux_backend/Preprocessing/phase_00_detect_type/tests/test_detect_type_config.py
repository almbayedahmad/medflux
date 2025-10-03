from __future__ import annotations

from medflux_backend.Preprocessing.phase_00_detect_type.connecters.detect_type_config_connector import (
    connect_detect_type_config_connector,
)


def test_detect_type_config_has_required_keys() -> None:
    cfg = connect_detect_type_config_connector()
    assert cfg.get("stage") == "detect_type"
    assert cfg["io"]["out_doc_path"].endswith("detect_type_unified_document.json")
    assert cfg["io"]["out_stats_path"].endswith("detect_type_stage_stats.json")
