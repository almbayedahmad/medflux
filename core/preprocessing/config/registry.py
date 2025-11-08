# PURPOSE:
#   Central registry and utilities for resolving per-phase configuration,
#   profiles, and overrides in a consistent manner.
#
# OUTCOME:
#   Reduces duplicated config loading/merging logic across phases and simplifies
#   testing and introspection of effective configuration.

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

_REGISTRY: Dict[str, Callable[[Optional[str]], Dict[str, Any]]] = {}


def register_phase_config(phase_id: str, loader: Callable[[Optional[str]], Dict[str, Any]]) -> None:
    """Register a configuration loader for a phase.

    Args:
        phase_id: Canonical id (e.g., "phase_01_encoding").
        loader: Callable accepting an optional profile name and returning config.
    Outcome:
        Allows late binding of phase configs without introducing tight coupling.
    """

    _REGISTRY[phase_id] = loader


def get_phase_config(phase_id: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """Resolve a phase's base configuration using a registered loader.

    Args:
        phase_id: Canonical id.
        profile: Optional profile name (e.g., "dev", "staging").
    Returns:
        A configuration mapping for the phase. If not registered, returns an
        empty dict to keep callers resilient.
    """

    loader = _REGISTRY.get(phase_id)
    if not loader:
        return {}
    return loader(profile)


def merge_overrides(base: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Deep-merge two dictionaries with a simple, predictable strategy.

    Dict values are merged recursively; other types are overwritten by
    `overrides`.

    Args:
        base: Baseline configuration.
        overrides: Optional overrides mapping.
    Returns:
        The merged configuration.
    """

    if not overrides:
        return dict(base)

    def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = _merge(out[k], v)  # type: ignore[index]
            else:
                out[k] = v
        return out

    return _merge(base, overrides)
