# PURPOSE:
#   Static safeguard: ensure no cross-phase domain/ops imports exist outside services.
# OUTCOME:
#   Enforces that cross-phase access uses service facades or phase public APIs, not domain/ops.

from __future__ import annotations

import re
from pathlib import Path


PATTERNS = (
    re.compile(r"(^|\s)(from|import)\s+backend\.Preprocessing\.phase_\d+_[^\s]+\.domain(\.|\s)"),
    re.compile(r"(^|\s)(from|import)\s+backend\.Preprocessing\.phase_\d+_[^\s]+\.domain\.ops(\.|\s)"),
)


def _is_allowed(path: Path) -> bool:
    """Return True for allowed locations (services and tests).

    The check normalizes absolute paths for cross-platform consistency and
    allows:
    - any files under `core/preprocessing/services/`
    - any files under `tests/`
    """
    try:
        p = path.as_posix()
        p = p.replace("\\", "/")
        return "/core/preprocessing/services/" in p or "/tests/" in p
    except Exception:
        return False


def test_no_cross_phase_domain_imports_outside_services() -> None:
    root = Path(".").resolve()
    violations: list[str] = []
    for py in root.rglob("*.py"):
        # skip venvs and hidden directories
        p_str = py.as_posix()
        if "/.venv/" in p_str or "/venv/" in p_str or "/.git/" in p_str or "/node_modules/" in p_str:
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for pat in PATTERNS:
            if pat.search(text):
                if not _is_allowed(py):
                    violations.append(p_str)
                    break
    assert not violations, f"cross-phase domain imports found outside services: {violations}"
