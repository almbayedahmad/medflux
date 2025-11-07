
# ✅ AGENTS MASTER POLICY (MedFlux)
This is the ONLY file Agents must read before generating, modifying, or deleting any code in the MedFlux project.

It includes:
1) Policy Digest
2) File Writing / Naming / Commenting Policy
3) Minimal Bootstrap Rules
4) Manifest Logic (Integrated)

============================================================
# ✅ 1. POLICY DIGEST (Key Rules – Must Always Be Enforced)
============================================================

### ✅ Core Rules
- No secrets or personal data in code or logs.
- Follow PEP8, PEP257, full type hints, and complete docstrings.
- Every new file must begin with:
  - **PURPOSE**
  - **OUTCOME**
  - (optional) INPUTS / OUTPUTS / DEPENDENCIES
- YAML must use UTF‑8, LF, 2 spaces indentation, single‑quoted regex.
- Logging must follow event_codes + redaction rules.
- README & CHANGELOG must be updated for any behavioral change.
- Git rules:
  - No commits directly to `main`
  - Use Conventional Commits (`feat:`, `fix:`, `docs:`, …)

### ✅ Before allowing a PR:
- pre-commit must pass
- pytest must pass
- yamllint on policy directory must pass

============================================================
# ✅ 2. FILE WRITING, NAMING & COMMENTING POLICY
============================================================

#
# FILE WRITING, NAMING & COMMENTING POLICY (MedFlux)
*(Mandatory for all Agents – focus on file creation, naming, comments, and explanation)*

This policy defines **how every new file must be written**, **how it must be named**, and **how code must be explained**.
It is short, strict, and immediately enforceable.

---

## 1) Scope (What this applies to)
- New **Python** files, modules, packages
- New **YAML/JSON** configs and schemas
- New **README/MD** files tied to code
- New **pipeline components** (readers, stages, adapters, connectors)
- Any file that affects execution or configuration

If a rule here conflicts with any other document, **this policy wins** for file writing, naming and commenting.

---

## 2) Naming Conventions (Folders, Files, Identifiers)
### 2.1 Folders & Files
- **snake_case** for Python files: `text_normalizer.py`, `pdf_reader.py`
- **snake_case** for directories: `io_readers`, `stage_builder`, `merge_cleaning`
- Tests mirror structure: `tests/unit/io_readers/test_pdf_reader.py`
- Avoid vague names: **no** `misc.py`, `helpers.py`, `new1.py`

### 2.2 Python Identifiers
- **Modules/Functions/Variables**: `snake_case`
- **Classes/Exceptions**: `PascalCase` → `DocumentParser`, `InvalidConfigError`
- **Constants**: `UPPER_SNAKE_CASE` → `DEFAULT_TIMEOUT = 30`
- **Private** (internal use): prefix underscore → `_normalize_text()`
- Keep names **short, descriptive, unambiguous** (max ~30 chars recommended)

### 2.3 Config Files
- YAML/JSON names reflect purpose: `event_codes.yaml`, `redaction_rules.yaml`, `reader_defaults.yaml`
- Schema files end with `_schema`: `stage_schema.yaml`, `entity_schema.json`

---

## 3) Required File Header (Every new file)
Every new file **must** start with a header block that states **Purpose** and **Outcome** (and key interfaces).

### 3.1 Python header (required)
```python
# PURPOSE:
#   What this module does and why it exists (1–3 lines).
#
# OUTCOME:
#   What it produces/changes and how it impacts the pipeline (1–3 lines).
#
# INPUTS:
#   Main inputs (types/paths) and assumptions.
#
# OUTPUTS:
#   Main outputs (types/paths) and guarantees.
#
# DEPENDENCIES:
#   Key modules/configs/events it requires (if any).
```

### 3.2 YAML/JSON header (required as comments/top keys)
```yaml
# PURPOSE: Defines validation for entity extraction.
# OUTCOME: Enforces structural consistency across entity definitions.
# INPUTS: Entities emitted by spans phase.
# OUTPUTS: Validated entity list with normalized types.
```

---

## 4) Docstrings & In‑line Comments
### 4.1 Docstring standard (Google-style)
Every **public** function/class **must** have a docstring that includes purpose, args, returns, raises, and outcome.

```python
def normalize_text(raw: str) -> str:
    """Normalize input text.

    Args:
        raw: Raw text extracted from a document.
    Returns:
        Clean, normalized text (unicode NFC, trimmed, single-spaced).
    Raises:
        ValueError: If `raw` is empty or only whitespace.
    Outcome:
        Produces stable text normalization for downstream readers.
    """
    if not raw or raw.isspace():
        raise ValueError("empty input")
    # collapse whitespace
    return " ".join(raw.split())
```

### 4.2 In‑line comments (when required)
Add short comments for **non-obvious logic**, **data transforms**, **validations**, **error handling**, and **edge cases**.
Prefer explaining **WHY** rather than **WHAT**.

```python
# Avoid re-decoding: content already normalized by upstream reader.
if already_normalized:
    return content
```

---

## 5) YAML/JSON Rules (Formatting & Safety)
- Encoding: **UTF‑8**, line endings: **LF only**
- Indentation: **2 spaces**, **no tabs**
- Block list:
  ```yaml
  items:
    - a
    - b
  ```
- Inline list: `[a, b]` (use commas)
- Regex/backslashes MUST be **single‑quoted**: `'\d{4}-\d{2}-\d{2}'`
- JSON must be valid (no comments), stable key order where applicable

---

## 6) Minimal Python Module Template (Ready to copy)
```python
# PURPOSE:
#   Short description of the module's responsibility.
# OUTCOME:
#   What this module returns/emits/changes for the pipeline.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class FooConfig:
    """Configuration for Foo."""
    enabled: bool = True
    threshold: float = 0.9

class FooError(Exception):
    """Domain-specific error for Foo."""

class Foo:
    """Execute Foo's main behavior.

    Args:
        cfg: Optional configuration for tuning behavior.
    Outcome:
        Produces processed items list suitable for phase N+1.
    """
    def __init__(self, cfg: FooConfig | None = None) -> None:
        self.cfg = cfg or FooConfig()

    def run(self, items: Iterable[Any]) -> list[Any]:
        """Run processing on items.

        Args:
            items: Iterable of inputs.
        Returns:
            A list of processed items.
        Raises:
            FooError: On domain violation or unrecoverable state.
        Outcome:
            Stable, validated outputs with deterministic ordering.
        """
        logger.info("foo.run.start", extra={"count": len(list(items))})
        try:
            return [self._process(x) for x in items]
        except Exception as exc:
            logger.exception("foo.run.failed")
            raise FooError(str(exc)) from exc

    def _process(self, x: Any) -> Any:
        # Explain any non-trivial logic here (why, not what).
        return x
```

---

## 7) Prohibited & Required Practices
### 7.1 Prohibited
- ❌ Generic names (`misc.py`, `utils.py`, `temp.py`)
- ❌ Functions or classes **without** docstrings
- ❌ Files **without** Purpose/Outcome header
- ❌ Tabs, CRLF, trailing spaces, unquoted regex in YAML
- ❌ Swallowing exceptions silently

### 7.2 Required
- ✅ Type hints everywhere in public API
- ✅ Domain‑specific exceptions + context
- ✅ Structured logging (no PII/secrets), map to event codes where applicable
- ✅ Clear input/output contracts in headers/docstrings

---

## 8) Acceptance Checklist (Gate before commit/PR)
- [ ] File name follows **snake_case** (Python) / clear purpose (YAML/JSON)
- [ ] File **header** has Purpose & Outcome (+ inputs/outputs/deps if relevant)
- [ ] All public functions/classes have **docstrings**
- [ ] Non‑obvious logic has **in‑line comments (WHY)**
- [ ] YAML/JSON formatting rules satisfied (UTF‑8, LF, 2 spaces, quoted regex)
- [ ] No secrets/PII; logs follow event/redaction policies
- [ ] Tests updated/added if required
- [ ] README/CHANGELOG updated if behavior changes
- [ ] Pre‑commit/linters/tests pass locally

---

## 9) Optional Automation Hints (lightweight, non‑blocking)
- Pre‑commit hook to check headers:
  - Python: ensure `# PURPOSE:` and `# OUTCOME:` within first 20 lines
  - YAML: `# PURPOSE:` and `# OUTCOME:` present at top
- Lint rule: reject files that violate naming or missing docstrings
- CI: fail on tabs/CRLF or unquoted regex in YAML

---

## 10) Final Rule
If any of the above are missing for a new file, **the file is non‑compliant** and must be fixed **before** merge.
This policy is **mandatory** for all Agents and supersedes style preferences.

============================================================
# ✅ 3. AGENT BOOTSTRAP (MINIMAL)
============================================================

### ✅ Before ANY development, the Agent MUST:
1. Read this entire file fully
2. Load and apply all rules in sections:
   - Policy Digest
   - File Writing/Naming/Commenting
3. Enforce acceptance rules
4. Confirm internally:

```
POLICY DIGEST LOADED.
FILE WRITING POLICY LOADED.
ALL RULES UNDERSTOOD.
DEVELOPMENT ALLOWED.
```

If ANY part of this file is missing, unreadable, or incomplete:
**STOP IMMEDIATELY.**

============================================================
# ✅ END OF AGENTS MASTER POLICY
============================================================
