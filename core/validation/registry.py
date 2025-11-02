from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def get_schema_root() -> Path:
    """Return the root directory for validation schemas.

    Overridable via env `MEDFLUX_SCHEMA_ROOT` (preferred) or legacy `MFLUX_SCHEMA_ROOT`;
    defaults to `core/validation/contracts`.
    Accepts absolute or workspace-relative paths.
    """
    env = (os.environ.get("MEDFLUX_SCHEMA_ROOT", "") or os.environ.get("MFLUX_SCHEMA_ROOT", "")).strip()
    if env:
        p = Path(env)
        return p if p.is_absolute() else Path.cwd() / p
    return Path("core") / "validation" / "contracts"


def discover_phase(phase: str, *, root: Optional[Path] = None) -> Dict[str, Path]:
    """Discover schema paths for a phase.

    Returns a dict with keys: input, output. Raises FileNotFoundError if missing.
    """
    base = (root or get_schema_root()) / "stages" / phase
    input_p = base / "input.schema.json"
    output_p = base / "output.schema.json"
    if not input_p.exists():
        raise FileNotFoundError(f"Phase input schema not found: {input_p}")
    if not output_p.exists():
        raise FileNotFoundError(f"Phase output schema not found: {output_p}")
    return {"input": input_p, "output": output_p}
