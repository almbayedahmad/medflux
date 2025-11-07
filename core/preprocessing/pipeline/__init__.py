"""Multi-phase pipeline orchestration entry points."""

from .preprocessing_chain import run_preprocessing_chain
from .detect_and_read import main as run_detect_and_read_cli

__all__ = ["run_preprocessing_chain", "run_detect_and_read_cli"]
