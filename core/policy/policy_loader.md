# Policy Consumption and Precedence

How code discovers and applies policies with predictable overrides.

- Locations (in order of precedence)
  1) Local overrides: `core/policy/rules.local.yaml` (developer machine) — optional
  2) Central policies: `core/policy/<domain>/<file>` — authoritative
  3) Defaults embedded in code (last resort)

- Loader Guidance
  - Resolve absolute path via repository root + `core/policy/...`
  - Parse YAML/MD as needed; validate structure when schemas exist
  - Merge: start from central policy, overlay keys from rules.local.yaml when present

- Example (Python pseudocode)
```python
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
policy_path = ROOT / 'core' / 'policy' / 'validation' / 'validation_rules.yaml'
overrides_path = ROOT / 'core' / 'policy' / 'rules.local.yaml'

policy = yaml.safe_load(policy_path.read_text())
if overrides_path.exists():
    overrides = yaml.safe_load(overrides_path.read_text()) or {}
    # shallow merge example; prefer domain-specific merging where needed
    policy.update(overrides.get('validation', {}))
```

- Do’s and Don’ts
  - Do: prefer read-only access to central policies in runtime
  - Do: keep overrides local and out of VCS
  - Don’t: duplicate policies under backend/apps once consumers repoint
