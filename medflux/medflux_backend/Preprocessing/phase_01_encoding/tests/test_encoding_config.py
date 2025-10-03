from __future__ import annotations

from medflux_backend.Preprocessing.phase_01_encoding.connecters.encoding_config_connector import (
    connect_encoding_config_connector,
)


def test_encoding_config_contains_outputs() -> None:
    cfg = connect_encoding_config_connector()
    assert cfg.get("stage") == "encoding"
    assert cfg["io"]["out_doc_path"].endswith("encoding_unified_document.json")
    assert cfg["io"]["out_stats_path"].endswith("encoding_stage_stats.json")
