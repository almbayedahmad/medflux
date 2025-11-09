# PURPOSE:
#   Backward-compat connector shim exposing readers config under connectors/.
# OUTCOME:
#   Allows v2 API to import from connectors while preserving legacy modules.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from core.preprocessing.config.registry import load_phase_defaults, merge_overrides


_STAGE_NAME = "readers"


def connect_readers_config_connector(stage_name: str = _STAGE_NAME) -> Dict[str, Any]:
    """Load and merge the readers phase configuration.

    Args:
        stage_name: Optional alternate stage name mapping to a YAML file.
    Returns:
        Effective configuration after merging centralized defaults with the
        phase-local YAML (if present).
    Outcome:
        Provides a single source for readers configuration resolution.
    """

    config_dir = Path(__file__).resolve().parent.parent / "config"
    candidates = [config_dir / "stage.yaml"]
    if stage_name and stage_name != _STAGE_NAME:
        candidates.insert(0, config_dir / f"{stage_name}.yaml")

    defaults = load_phase_defaults()
    for candidate in candidates:
        if candidate.exists():
            cfg = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return merge_overrides(defaults, cfg)

    raise FileNotFoundError(f"No configuration file found for stage '{stage_name}' in {config_dir}")

__all__ = ["connect_readers_config_connector"]
