from __future__ import annotations

"""Stage-local reader runtime settings."""

from dataclasses import dataclass
from typing import Any, Dict

from ..config_profiles.profiles_loader import CFG


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Snapshot of runtime feature flags and thresholds."""

    thresholds: Dict[str, Any]
    features: Dict[str, Any]


def get_runtime_settings() -> RuntimeSettings:
    """Return the runtime settings snapshot for the readers stage."""

    thresholds = dict(CFG.get("thresholds") or {})
    features = dict(CFG.get("features") or {})
    return RuntimeSettings(thresholds=thresholds, features=features)


# Backwards-compatible aliases
ReadersRuntimeSettings = RuntimeSettings
get_readers_runtime_settings = get_runtime_settings


__all__ = [
    "RuntimeSettings",
    "ReadersRuntimeSettings",
    "get_runtime_settings",
    "get_readers_runtime_settings",
]
