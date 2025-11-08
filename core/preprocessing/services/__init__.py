# PURPOSE:
#   Mark the services package exposing cross-phase capabilities via stable
#   interfaces (e.g., detect/encoding/readers), reducing direct imports.
#
# OUTCOME:
#   Enables `core.preprocessing.services` consumers to rely on stable methods
#   instead of importing implementation details from other phases.

from __future__ import annotations

__all__: list[str] = []
