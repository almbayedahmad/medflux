"""Versioning utilities for the core package.

Centralizes version discovery and helpers so all layers can consistently
report and check the running version.
"""

from __future__ import annotations

from importlib import resources
import os
import subprocess
from typing import Dict, Optional

from .schemas import get_schema_version, validate_contract_version  # re-export

__all__ = [
    "__version__",
    "get_version",
    "get_version_info",
    "make_artifact_stamp",
    "get_schema_version",
    "validate_contract_version",
]


def _read_version_file() -> Optional[str]:
    try:
        with resources.files(__package__).joinpath("VERSION").open("r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


__version__ = _read_version_file() or "0.1.0"


def get_version() -> str:
    return __version__


def _get_git_sha_short() -> Optional[str]:
    env_sha = os.environ.get("BUILD_GIT_SHA")
    if env_sha:
        return env_sha[:7]
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None


def get_version_info() -> Dict[str, Optional[str]]:
    """Return version details including optional build metadata.

    Fields:
    - version: semantic version from VERSION file
    - git_sha: short commit SHA if available
    - build_number: CI build number if provided (BUILD_NUMBER)
    - build_date: ISO date if provided (BUILD_DATE)
    """

    return {
        "version": get_version(),
        "git_sha": _get_git_sha_short(),
        "build_number": os.environ.get("BUILD_NUMBER"),
        "build_date": os.environ.get("BUILD_DATE"),
    }


def make_artifact_stamp(*, schema_name: str | None = None) -> dict:
    """Return a standard stamp for embedding into produced JSON artifacts.

    Includes app version and optional schema version information.
    """
    info = get_version_info()
    stamp = {
        "app_version": info.get("version"),
        "git_sha": info.get("git_sha"),
        "build_number": info.get("build_number"),
        "build_date": info.get("build_date"),
    }
    if schema_name:
        from .schemas import get_schema_version

        stamp["schema_name"] = schema_name
        stamp["schema_version"] = get_schema_version(schema_name)
    return {"versioning": stamp}
