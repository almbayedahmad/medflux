"""Ensure core test dependencies are available without reinstalling unnecessarily."""

from __future__ import annotations

import importlib.util
import subprocess
import sys

REQUIRED = ("pytest", "pytest-cov")


def main() -> None:
    missing = []
    for pkg in REQUIRED:
        module_name = pkg.replace("-", "_")
        if importlib.util.find_spec(module_name) is None:
            missing.append(pkg)

    if not missing:
        return

    print(f"Installing: {missing}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


if __name__ == "__main__":
    main()
