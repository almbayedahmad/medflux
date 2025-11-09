# PURPOSE:
#   Pre-commit hook that forbids adding new imports that reference the legacy
#   'connecters' package path. It checks only newly added lines in staged
#   Python files to avoid flagging existing code during migration.
#
# OUTCOME:
#   Prevents regression by blocking new usages while allowing existing
#   references to be refactored incrementally.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


PATTERN = re.compile(r"(^|\s)(from|import)\s+.*\.connecters(\.|\s)")


def _added_lines_diff(file: Path) -> Iterable[str]:
    """Yield added lines from the staged diff for a file."""

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
        for added in _added_lines_diff(path):
            if PATTERN.search(added):
                sys.stderr.write(f"forbid-connecters-imports: {path}: {added}\n")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
