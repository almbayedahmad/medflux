from __future__ import annotations

"""Configuration connector for the encoding stage."""

from pathlib import Path
from typing import Any, Dict

import yaml
from core.preprocessing.config.registry import load_phase_defaults, merge_overrides


def connect_encoding_config_connector(stage_name: str = "encoding") -> Dict[str, Any]:
    """Load and merge the encoding phase configuration.

    Args:
        stage_name: Optional alternate stage name mapping to a YAML file.
    Returns:
        Effective configuration after merging centralized defaults with the
        phase-local YAML (if present).
    Outcome:
        Single source of truth for encoding configuration resolution.
    """

    base_dir = Path(__file__).resolve().parent.parent
    config_dir = base_dir / "config"
    candidates = [config_dir / "stage.yaml"]
    if stage_name and stage_name != "encoding":
        candidates.insert(0, config_dir / f"{stage_name}.yaml")

    defaults = load_phase_defaults()
    for candidate in candidates:
        if candidate.exists():
            cfg = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return merge_overrides(defaults, cfg)

    raise FileNotFoundError(f"No configuration file found for stage '{stage_name}' in {config_dir}")
