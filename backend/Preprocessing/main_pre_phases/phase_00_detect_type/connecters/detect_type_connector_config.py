from __future__ import annotations

"""Configuration connector for the detect_type stage."""

from pathlib import Path
from typing import Any, Dict

import yaml


def connect_detect_type_config_connector(stage_name: str = "detect_type") -> Dict[str, Any]:
    """Load the stage configuration according to the standards."""

    base_dir = Path(__file__).resolve().parent.parent
    config_dir = base_dir / "config"
    candidate_files = [config_dir / "stage.yaml"]
    if stage_name and stage_name != "detect_type":
        candidate_files.insert(0, config_dir / f"{stage_name}.yaml")

    for candidate in candidate_files:
        if candidate.exists():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}

    raise FileNotFoundError(f"No configuration file found for stage '{stage_name}' in {config_dir}")
