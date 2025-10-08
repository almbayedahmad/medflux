from __future__ import annotations

"""Configuration connector for the readers stage."""

from pathlib import Path
from typing import Any, Dict

import yaml


_STAGE_NAME = "readers"


def connect_readers_config_connector(stage_name: str = _STAGE_NAME) -> Dict[str, Any]:
    config_dir = Path(__file__).resolve().parent.parent / "config"
    candidates = [config_dir / "stage.yaml"]
    if stage_name and stage_name != _STAGE_NAME:
        candidates.insert(0, config_dir / f"{stage_name}.yaml")

    for candidate in candidates:
        if candidate.exists():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}

    raise FileNotFoundError(f"No configuration file found for stage '{stage_name}' in {config_dir}")

