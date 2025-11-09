# PURPOSE:
#   Pre-commit hook that validates file headers for MedFlux policy compliance.
# OUTCOME:
#   Blocks commits that add Python/YAML files without the required PURPOSE/OUTCOME header.
# INPUTS:
#   Receives staged file paths from pre-commit. Only checks added/modified files.
# OUTPUTS:
#   Non-zero exit code on violations with a helpful error message.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


PYTHON_HEADER_MARKERS = ("# PURPOSE:", "# OUTCOME:")
YAML_HEADER_MARKERS = ("# PURPOSE:", "# OUTCOME:")


def _head_lines(path: Path, max_lines: int = 25) -> list[str]:
    try:
        # Read a small head slice only
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines: list[str] = []
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n\r"))
            return lines
    except Exception:
        return []


def _needs_check(path: Path) -> bool:
    # Check only python and yaml/yml files within repo sources, skip third-party/vendor directories
    if path.suffix.lower() in {".py", ".yaml", ".yml"}:
        # Skip virtualenvs and hidden folders
        parts = {p.lower() for p in path.parts}
        if any(x in parts for x in {".venv", "venv", "node_modules", ".git"}):
            return False
        return True
    return False


def _has_required_header(path: Path) -> bool:
    lines = _head_lines(path)
    if path.suffix.lower() == ".py":
        return all(any(marker in line for line in lines) for marker in PYTHON_HEADER_MARKERS)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return all(any(marker in line for line in lines) for marker in YAML_HEADER_MARKERS)
    return True


def main(argv: list[str]) -> int:
    failed = False
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            # Deleted or renamed, ignore
            continue
        if not _needs_check(path):
            continue
        if not _has_required_header(path):
            sys.stderr.write(
                f"check-headers: missing PURPOSE/OUTCOME header in {path}\n"
            )
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
