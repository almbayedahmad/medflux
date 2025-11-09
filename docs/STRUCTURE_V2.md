# PURPOSE:
#   Describe the MedFlux v2 repository structure, boundaries, and rules.
# OUTCOME:
#   Provides a concise reference for contributors to navigate the codebase and
#   follow policy-compliant development practices.

## Layout (Top-Level)
- `backend/Preprocessing/phase_XX_<name>/` — all phases (00–10)
  - `api.py` — public PhaseRunner API wrapper
  - `cli/` — thin v2 CLI wrapper using `core.preprocessing.cli.common`
  - `connectors/` — config + upstream connectors (merge defaults)
  - `domain/` — core processing logic (no cross-phase imports)
  - `io/` — writers only (no business logic)
  - `schemas/` — phase-specific types/contracts
  - `common_files/` — docs + configs + Makefile stubs
- `core/` — shared libraries (policy, logging, services, config registry, pipeline)
- `tests/` — all executable tests (unit, component, contract, golden, integration, e2e)
- `tools/` — generators, maintenance scripts, dev tools

## Boundaries & Rules
- No cross-phase `domain/` or `domain/ops/` imports. Use `core.preprocessing.services.*` or phase public APIs.
- Phase connectors must merge `core/preprocessing/cross_phase/config/phase_defaults.yaml` via registry helpers.
- Writers must stamp artifacts with schema names; register schema versions in `core/versioning/schemas.yaml`.
- Policy-driven logging: apply via `core.logging.configure_logging()`; use v2 categories (`domain`, `cli`, `io`, `connectors`, `schemas`, `tests`).
- Tests live under root `tests/` only. No `phase_XX/tests/` folders.

## CLI
- Prefer umbrella CLI `medflux` for operators and smoke runs.
- Phase-local v2 CLIs remain available for targeted runs and development.
- Chain runner: opt-in flags to include phases beyond readers.

## Services
- Facades under `core/preprocessing/services/*` provide stable cross-phase access.
- Keep payloads small and stable; avoid importing phase domains from outside services.

## Contracts
- Stage schemas under `core/validation/contracts/stages/<phase>/`.
- Artifact schemas under `core/validation/contracts/artifacts/<phase>/` (as phases emit outputs).
- Contract tests validate schema correctness and stamping.

## Defaults
- Central defaults at `core/preprocessing/cross_phase/config/phase_defaults.yaml`.
- Per-phase overrides live under `phase_XX_*/config/stage.yaml` and must stay minimal.

## CI & Gates
- Pre-commit hooks: forbid legacy imports, cross-phase domain imports, phase-local tests, enforce headers, yamllint.
- CI audits: legacy patterns, tracked caches/logs, phase-local tests in filesystem.
- Smoke jobs: umbrella CLI phase-list and quick detect; umbrella chain flags exercise more phases as they mature.
