# PURPOSE:
#   Repository cleanup utility to remove unneeded/cached directories and legacy
#   artifacts (outputs, logs, caches, phase-local tests).
#
# OUTCOME:
#   Provides a consistent, cross-platform cleanup script that developers can run
#   locally or in CI to enforce a tidy workspace aligned with v2 structure.
#
# INPUTS:
#   Optional CLI flags:
#     --yes / -y     Proceed without interactive prompt.
#     --dry-run      Print what would be removed without deleting.
#     --verbose      Print each removed path.
#
# OUTPUTS:
#   Prints a summary of removed directories/files.

from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Target:
    """A removable target path pattern.

    Attributes:
        pattern: Path or glob-like pattern relative to repo root.
        is_dir: Whether the target is a directory (True) or file (False).
    """

    pattern: str
    is_dir: bool = True


TARGETS: Sequence[Target] = (
    # Root legacy or transient dirs
    Target("outputs"),
    Target("logs"),
    Target(".artifacts"),
    Target("ci_artifacts"),
    # Common caches
    Target("**/__pycache__"),
    Target("**/.pytest_cache"),
    Target("**/.benchmarks"),
    # Phase-local tests (not allowed in v2)
    Target("backend/Preprocessing/phase_*/tests"),
)


def find_matches(root: Path, target: Target) -> List[Path]:
    """Return a list of matching paths for the given target pattern."""

    matches: List[Path] = []
    # Use rglob for patterns with '**' or '*', else direct check
    if any(ch in target.pattern for ch in ("*", "?")):
        for path in root.glob(target.pattern):
            matches.append(path)
    else:
        path = root / target.pattern
        if path.exists():
            matches.append(path)
    return matches


def remove_path(path: Path, verbose: bool = False) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except TypeError:
                if path.exists():
                    path.unlink()
        if verbose:
            print(f"removed: {path}")
    except Exception as exc:  # pragma: no cover - best effort cleanup
        if verbose:
            print(f"skip (error): {path} -> {exc}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MedFlux repository cleanup")
    parser.add_argument("--yes", "-y", action="store_true", help="Proceed without interactive prompt")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be removed without deleting")
    parser.add_argument("--verbose", action="store_true", help="Print each removed path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(os.getcwd()).resolve()
    to_remove: List[Path] = []
    for target in TARGETS:
        to_remove.extend(find_matches(root, target))

    # De-duplicate and sort (longer paths last not necessary, but stable order helps)
    unique = sorted({p.resolve() for p in to_remove})
    if args.dry_run:
        print("[dry-run] would remove:")
        for p in unique:
            print(f"  {p}")
        return 0

    if not args.yes:
        print("About to remove the following paths:")
        for p in unique:
            print(f"  {p}")
        confirm = input("Proceed? [y/N]: ").strip().lower()
        if confirm not in {"y", "yes"}:
            print("Aborted.")
            return 1

    removed = 0
    for p in unique:
        remove_path(p, verbose=args.verbose)
        removed += 1
    print(f"Cleanup complete. Removed {removed} paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
