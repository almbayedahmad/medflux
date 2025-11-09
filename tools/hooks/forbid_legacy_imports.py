# PURPOSE:
#   Pre-commit hook that forbids adding new imports referencing legacy phase
#   packages: internal_helpers/, core_functions/, or pipeline_workflow/.
#
# OUTCOME:
#   Prevents regressions by blocking new usages of deprecated paths while we
#   migrate code to v2 domain/connectors/io structures and services.
#
# INPUTS:
#   - CLI arguments from pre-commit with candidate file paths.
#
# OUTPUTS:
#   - Non-zero exit code on violations; prints offending lines.
#
# DEPENDENCIES:
#   - git is expected to be available for diffing staged changes.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


PATTERN = re.compile(r"(^|\s)(from|import)\s+.*\.(internal_helpers|core_functions|pipeline_workflow)(\.|\s)")


def _added_lines_diff(file: Path) -> Iterable[str]:
    """Yield added lines from the staged diff for a file.

    This focuses on added lines only to avoid flagging existing code that
    will be migrated incrementally.
    """

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
        # Only checks Python files
        if path.suffix != ".py":
            continue
        for added in _added_lines_diff(path):
            if PATTERN.search(added):
                sys.stderr.write(f"forbid-legacy-imports: {path}: {added}\n")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
