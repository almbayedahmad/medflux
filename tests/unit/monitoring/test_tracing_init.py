from __future__ import annotations

import importlib

import pytest


def test_tracing_init_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # Explicitly disabled via MEDFLUX_TRACING=0
    monkeypatch.setenv("MEDFLUX_TRACING", "0")
    mod = importlib.import_module("core.monitoring.tracing")
    importlib.reload(mod)
    mod.init_tracer()
    assert mod.get_tracer() is None


def test_tracing_init_no_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure calling init twice does not crash even if OTEL missing
    mod = importlib.import_module("core.monitoring.tracing")
    importlib.reload(mod)
    mod.init_tracer()
    mod.init_tracer()
    # get_tracer may be None when OTEL is not installed; assert it doesn't error
    _ = mod.get_tracer()

