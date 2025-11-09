# PURPOSE:
#   Minimal config connector for phase_08_heavy_normalization (v2 scaffold).
# OUTCOME:
#   Returns a placeholder configuration mapping.

from __future__ import annotations

from typing import Any, Dict
from pathlib import Path
import yaml
from core.preprocessing.config.registry import load_phase_defaults, merge_overrides


def connect_heavy_normalization_config_connector(stage_name: str = "heavy_normalization") -> Dict[str, Any]:
    """Return the effective configuration for the heavy_normalization phase.

    Args:
        stage_name: Optional stage alias for future expansion.
    Returns:
        Minimal configuration merged with centralized defaults.
    Outcome:
        Keeps v2 scaffolds consistent while avoiding duplicated defaults.
    """

    defaults = load_phase_defaults()
    cfg_dir = Path(__file__).resolve().parent.parent / "config"
    candidates = [cfg_dir / "stage.yaml"]
    if stage_name:
        candidates.insert(0, cfg_dir / f"{stage_name}.yaml")
    for candidate in candidates:
        if candidate.exists():
            data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return merge_overrides(defaults, data)
    return merge_overrides(defaults, {"stage": stage_name, "io": {}, "options": {}})
