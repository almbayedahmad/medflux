from __future__ import annotations

import logging
from pathlib import Path

import pytest

import core.logging as clog


@pytest.mark.unit
def test_policy_without_root_adds_default_console(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Stub load_policy_with_overrides to return config without 'root'
    def fake_load_policy(path: str):  # type: ignore[no-untyped-def]
        return {
            "logging": {
                "version": 1,
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": "INFO",
                        "formatter": "standard",
                        "stream": "ext://sys.stdout",
                    }
                },
                "formatters": {"standard": {"format": "%(message)s"}},
            }
        }

    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "dev")
    monkeypatch.setenv("MEDFLUX_LOG_FILE", "0")
    # Reset root
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    monkeypatch.setattr(clog, "load_policy_with_overrides", fake_load_policy)
    clog.configure_logging(force=True)
    # Root should have a console handler present
    assert any(isinstance(h, logging.StreamHandler) for h in logging.getLogger().handlers)
