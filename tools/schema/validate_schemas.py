#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import runpy


if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    runpy.run_path(str(repo_root / "tools" / "validation" / "validate_schemas.py"), run_name="__main__")
