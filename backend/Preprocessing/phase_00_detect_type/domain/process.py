# PURPOSE:
#   Domain processing entrypoint for phase_00_detect_type (v2 layout wrapper).
# OUTCOME:
#   Re-exports the classifier function from legacy module to keep behavior while
#   adopting the new directory structure.

from __future__ import annotations

from typing import Any, Dict, Sequence

from .detect_classifier import process_detect_type_classifier  # noqa: F401

__all__ = ["process_detect_type_classifier"]
