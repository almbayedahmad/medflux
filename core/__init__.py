# PURPOSE:
#   Mark the top-level core package and provide a stable namespace root for
#   imports like `core.preprocessing.output.output_router` across environments.
#
# OUTCOME:
#   Ensures Python treats `core` as a package (not just a namespace),
#   eliminating ModuleNotFoundError scenarios in CI where implicit namespace
#   handling may differ.

from __future__ import annotations

"""Core package marker for MedFlux.

This module intentionally contains no runtime logic; it exists to make the
`core` directory an explicit Python package to improve portability across
environments and runners.
"""
