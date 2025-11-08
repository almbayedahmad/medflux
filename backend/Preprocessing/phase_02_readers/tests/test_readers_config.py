from __future__ import annotations

from backend.Preprocessing.phase_02_readers.connecters.readers_connector_config import (
    connect_readers_config_connector,
)


def test_readers_config_defaults() -> None:
    cfg = connect_readers_config_connector()
    assert "io" in cfg
    assert "options" in cfg
    assert cfg["io"]["out_root"].startswith("outputs/")
