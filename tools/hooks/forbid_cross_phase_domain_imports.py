# PURPOSE:
#   Pre-commit hook to forbid direct cross-phase imports of domain/ops modules.
# OUTCOME:
#   Enforces using `core.preprocessing.services.*` or phase public APIs instead
#   of importing `backend.Preprocessing.phase_XX_*/domain` or `/domain/ops` from
#   other phases.
# INPUTS:
#   Receives staged files from pre-commit and inspects added lines only.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


# Match any import referencing phase_XX_* domain or ops modules
PATTERN = re.compile(
    r"(^|\s)(from|import)\s+backend\.Preprocessing\.phase_\d+_[^\s]+\.(domain(\.ops)?)"
)


def _added_lines_diff(file: Path) -> Iterable[str]:
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", str(file)],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    for line in (proc.stdout or "").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield line[1:]


def main(argv: list[str]) -> int:
    failed = False
    for fname in argv[1:]:
        path = Path(fname)
        if path.suffix != ".py":
            continue
        # Allow imports within services package and tests
        p_str = path.as_posix()
        if p_str.startswith("core/preprocessing/services/") or p_str.startswith("tests/"):
            continue
        for added in _added_lines_diff(path):
            if PATTERN.search(added):
                sys.stderr.write(
                    f"forbid-cross-phase-domain-imports: {path}: {added}\n"
                )
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
