Central versioning utilities for the repository.

What lives here
- VERSION — single source of truth for the code version.
- __init__.py — accessors: `get_version()`, `get_version_info()`.
- __main__.py — CLI: `python -m core.versioning` prints JSON info.
- schemas.yaml (optional) — registry for contract/schema versions.

Quick usage
- In code: `from core.versioning import get_version` → string like `0.1.0`.
- In logs: CoreLoader injects `version` context automatically.
- CLI: `python -m core.versioning` → `{ "version": "0.1.0", ... }`.

Bumping the version
- Script: `python tools/versioning/bump_version.py [major|minor|patch]`.
- This updates `core/versioning/VERSION` only (keep it simple for now).

Notes
- Build metadata fields (git sha, build number/date) are read from env when available and surfaced by `get_version_info()`.
- Schema registry is optional; wire it in where contracts are loaded if needed.
