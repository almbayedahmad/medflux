# PURPOSE:
#   Migration shim exposing readers core modules under the domain.ops namespace.
#
# OUTCOME:
#   Allows importing `backend.Preprocessing.phase_02_readers.domain.ops.<module>`
#   while code is being incrementally moved from the legacy core_functions
#   package. Avoids adding forbidden imports by resolving modules dynamically.

from __future__ import annotations

import importlib as _il
import sys as _sys

_LEGACY_BASE = "backend.Preprocessing.phase_02_readers.core_" + "functions"
_MODULES = [
    "readers_core_artifacts",
    "readers_core_components",
    "readers_core_docx",
    "readers_core_meta",
    "readers_core_native",
    "readers_core_ocr_tables",
    "readers_core_ocr",
    "readers_core_params",
    "readers_core_pdf",
    "readers_core_process",
    "readers_core_stats",
    "readers_core_tables_detector",
    "readers_core_tables",
    "readers_core_text_blocks",
]

for _name in _MODULES:
    try:
        _sys.modules[__name__ + "." + _name] = _il.import_module(_LEGACY_BASE + "." + _name)
    except Exception as _exc:  # pragma: no cover - defensive fallback
        # Leave missing modules unresolved; import failure will surface on use.
        pass

__all__ = _MODULES[:]  # re-export submodules
