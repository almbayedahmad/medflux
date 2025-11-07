"""Ensure core test dependencies are available without reinstalling unnecessarily."""

from __future__ import annotations

import importlib.util
import subprocess
import sys

# (module_name, pip_package)
REQUIRED = (
    ("pytest", "pytest"),
    ("pytest_cov", "pytest-cov"),
    ("jsonschema", "jsonschema"),
)


def missing_packages() -> list[str]:
    missing: list[str] = []
    for module_name, package_name in REQUIRED:
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def main() -> None:
    missing = missing_packages()
    if missing:
        print(f"Installing core test deps: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    else:
        print("All core test dependencies already installed.")


if __name__ == "__main__":
    main()
