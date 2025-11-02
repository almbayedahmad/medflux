from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_schema(path: Path) -> Dict[str, Any]:
    """Load a JSON or YAML schema from path.

    Supports .json, .yaml, .yml extensions.
    """
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8")) or {}
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PyYAML is required to load YAML schemas") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
    raise ValueError(f"Unsupported schema extension: {path}")
