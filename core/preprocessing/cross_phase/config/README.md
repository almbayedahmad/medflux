# MedFlux Cross‑Phase Defaults (Config)

## Purpose
Provide a single source of truth for baseline configuration shared across preprocessing phases (IO and options). Phase connectors load these defaults and deep‑merge lightweight per‑phase overrides.

## Files
- `phase_defaults.yaml` — central defaults merged into every phase.

## How it works
- Every phase connector calls:
  - `from core.preprocessing.config.registry import load_phase_defaults, merge_overrides`
  - Loads central defaults, then merges per‑phase overrides from `config/stage.yaml` (when present) or lightweight in‑code fallbacks.
- Merge semantics:
  - Dict values are merged recursively; non‑dict values are overwritten by overrides.

## Minimal per‑phase overrides
Keep per‑phase configs small — only include true deltas from the defaults. A minimal `config/stage.yaml` looks like:

```yaml
# PURPOSE: Minimal per-phase config overrides.
# OUTCOME: Merged with centralized defaults to form effective configuration.
stage: "<stage_name>"
io: {}
options: {}
```

## YAML rules (Policy)
- UTF‑8, LF line endings
- 2 spaces indentation, no tabs
- Regex/backslashes must be single‑quoted
- Prefer block lists for readability

## Example connector usage
```python
from core.preprocessing.config.registry import load_phase_defaults, merge_overrides
from pathlib import Path
import yaml

CFG_DIR = Path(__file__).resolve().parent.parent / "config"

def load_effective_config(stage_name: str, fallback: dict[str, object] | None = None) -> dict[str, object]:
    defaults = load_phase_defaults()
    candidates = [CFG_DIR / "stage.yaml"]
    if stage_name:
        candidates.insert(0, CFG_DIR / f"{stage_name}.yaml")
    for candidate in candidates:
        if candidate.exists():
            data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            return merge_overrides(defaults, data)
    return merge_overrides(defaults, fallback or {"stage": stage_name, "io": {}, "options": {}})
```

## Notes
- If a phase doesn’t need overrides yet, you can omit `stage.yaml` — the connector should still return a valid merged config.
- Defaults should remain conservative to avoid surprising behavior in early development.
