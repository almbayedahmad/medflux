# PURPOSE:
#   Pre-commit hook that forbids adding tests directories under phase folders.
# OUTCOME:
#   Enforces the policy that all tests live under root `tests/`.
# INPUTS:
#   Receives staged file paths from pre-commit.

from __future__ import annotations

import re
import sys
from pathlib import Path


PHASE_TESTS_RE = re.compile(r"backend[\\/]+Preprocessing[\\/]+phase_\d+_[^\\/]+[\\/]+tests[\\/]")


def main(argv: list[str]) -> int:
    failed = False
    for arg in argv[1:]:
        p = Path(arg)
        # The check is path-based; even creating an empty file under that dir violates the policy
        if PHASE_TESTS_RE.search(str(p)):
            sys.stderr.write(f"forbid-phase-local-tests: {p}\n")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
