# PURPOSE:
#   Backward-compat connector shim exposing the detect_type config loader
#   under the new connectors/ package.
# OUTCOME:
#   Allows v2 API to import from connectors while preserving legacy modules.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from core.preprocessing.config.registry import load_phase_defaults, merge_overrides


def connect_detect_type_config_connector(stage_name: str = "detect_type") -> Dict[str, Any]:
    """Load the stage configuration according to the standards."""

    base_dir = Path(__file__).resolve().parent.parent
    config_dir = base_dir / "config"
    candidate_files = [config_dir / "stage.yaml"]
    if stage_name and stage_name != "detect_type":
        candidate_files.insert(0, config_dir / f"{stage_name}.yaml")

    # Load defaults first
    defaults = load_phase_defaults()

    for candidate in candidate_files:
        if candidate.exists():
            cfg = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return merge_overrides(defaults, cfg)

    raise FileNotFoundError(f"No configuration file found for stage '{stage_name}' in {config_dir}")

__all__ = ["connect_detect_type_config_connector"]
