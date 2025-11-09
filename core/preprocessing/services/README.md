# PURPOSE:
#   Design rules for cross-phase service facades.
# OUTCOME:
#   Ensures stable, decoupled cross-phase usage via `core.preprocessing.services.*`.

## Principles
- Do not import another phase's `domain/` or `domain/ops/` from outside this package. Use service facades or phase public APIs instead.
- Services may import a phase's domain modules inside function bodies to minimize import-time coupling.
- Keep payloads small and stable; return plain dicts or typed dataclasses safe for cross-boundary usage.
- Prefer calling phase public APIs (`backend.Preprocessing.phase_XX_*.api`) when executing a phase, not domain internals.

## Existing facades
- `detect.DetectService`: file detection metadata from phase 00
- `encoding.EncodingService`: encoding metadata from phase 01
- `readers.ReadersService`: run metadata and detect/encoding digests
- Placeholders for future reuse: `merge`, `cleaning`, `segmentation`, `table_extraction`, `heavy_normalization`, `provenance`, `offsets`

## Tests & Enforcement
- Pre-commit hook `forbid_cross_phase_domain_imports` blocks added lines with forbidden imports.
- CI audits and unit test `tests/unit/services/test_cross_phase_imports.py` ensure no cross-phase domain imports exist outside services.
