# PURPOSE:
#   Deprecation shim for readers core process module under domain.ops.
#+ OUTCOME:
#   Provides a stable import that redirects to the v2 domain implementation
#   while signaling deprecation to callers.
#
# INPUTS:
#   - Same as domain.process (generic items).
#
# OUTPUTS:
#   - Re-exports process function and error type; no direct IO.
#
# DEPENDENCIES:
#   - Local domain.process; standard library warnings.
from __future__ import annotations

"""Deprecated readers core processing module (shim).

Re-exports the v2 domain implementation and emits a DeprecationWarning on
import. Use `backend.Preprocessing.phase_02_readers.domain.process` instead.
"""

import warnings as _warnings

_warnings.warn(
    "Deprecated module: backend.Preprocessing.phase_02_readers.domain.ops.readers_core_process. "
    "Use backend.Preprocessing.phase_02_readers.domain.process instead.",
    DeprecationWarning,
    stacklevel=2,
)

from ..domain.process import ReadersSegmentError, process_readers_segment  # noqa: F401,E402

__all__ = ["ReadersSegmentError", "process_readers_segment"]
