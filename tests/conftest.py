import logging
import os
import random
from pathlib import Path
from typing import Optional

import pytest
import sys


# Ensure repository root is importable for 'core', 'backend', and 'tests' namespace
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _seed_all(seed: int = 1337) -> None:
    random.seed(seed)
    try:
        import numpy  # type: ignore

        numpy.random.seed(seed)  # type: ignore[attr-defined]
    except Exception:
        pass


def _setup_logging() -> None:
    level_name = os.environ.get("PYTEST_LOGLEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _tests_root() -> Path:
    return Path.cwd() / "tests"


def _marker_for_path(p: Path) -> str:
    root = _tests_root()
    try:
        rel = p.resolve().relative_to(root.resolve())
    except Exception:
        return "unit"
    first: Optional[str] = rel.parts[0] if rel.parts else None
    mapping = {
        "unit": "unit",
        "component": "component",
        "contract": "contract",
        "integration": "integration",
        "golden": "golden",
        "smoke": "smoke",
        "e2e": "e2e",
        "perf": "perf",
    }
    return mapping.get(first or "", "unit")


def pytest_sessionstart(session: pytest.Session) -> None:  # noqa: D401
    # Silence OTEL exporters unless explicitly enabled
    os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
    os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
    _seed_all()
    _setup_logging()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        try:
            p = Path(str(item.fspath))
        except Exception:
            continue
        marker_name = _marker_for_path(p)
        item.add_marker(getattr(pytest.mark, marker_name))
