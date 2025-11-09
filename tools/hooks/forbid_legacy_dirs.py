# PURPOSE:
#   Pre-commit hook to prevent reintroducing legacy directories in the repo tree.
# OUTCOME:
#   Fails when files are added under forbidden paths like `outputs/` or
#   deprecated legacy structures.
# INPUTS:
#   Receives staged file paths from pre-commit.

from __future__ import annotations

import sys
from pathlib import Path


FORBIDDEN_TOP_LEVEL = {"connecters", "outputs"}
FORBIDDEN_ANYWHERE = {"internal_helpers", "core_functions", "pipeline_workflow"}


def _violates(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    # Top-level dir check
    if len(parts) > 0 and parts[0] in FORBIDDEN_TOP_LEVEL:
        return True
    # Anywhere in the tree
    return any(seg in FORBIDDEN_ANYWHERE for seg in parts)


def main(argv: list[str]) -> int:
    failed = False
    for arg in argv[1:]:
        p = Path(arg)
        if not p.exists():
            continue
        if _violates(p):
            sys.stderr.write(f"forbid-legacy-dirs: {p}\n")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
