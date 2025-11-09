from __future__ import annotations

from backend.Preprocessing.phase_02_readers.connectors.config import (
    connect_readers_config_connector,
)


def test_readers_config_defaults() -> None:
    cfg = connect_readers_config_connector()
    assert "io" in cfg
    assert "options" in cfg
    assert cfg["io"]["out_root"].startswith("outputs/")
