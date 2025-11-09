# Contributing to MedFlux

## Purpose
This guide explains how to contribute new code and phases to MedFlux following the v2 structure and policy.

## Quick Start
- Install dependencies: `pip install -r requirements.txt` (plus dev requirements if present)
- Run pre-commit once: `pre-commit install && pre-commit run -a`
- Run tests: `pytest -q`

## Structure v2
See `docs/STRUCTURE_V2.md` for the high-level layout and boundaries.

## Phase Development
- Use the generator: `python tools/preprocessing/phase_generator.py <num> <name>`
- The generator emits:
  - `api.py` (PhaseRunner wrapper)
  - `cli/*_cli_v2.py` (thin v2 CLI)
  - `connectors/` (config + upstream; merges central defaults)
  - `domain/` (core logic; no cross-phase imports)
  - `io/` (writers only; add stamped artifacts here)
  - `schemas/` (phase types/contracts)
  - `common_files/` (docs + configs + Makefile stub)
- All tests go under root `tests/` (no phase-local tests/ directories).

## Config & Defaults
- Central defaults live at `core/preprocessing/cross_phase/config/phase_defaults.yaml`.
- Phase connector pattern:
  - `defaults = load_phase_defaults()` then `merge_overrides(defaults, local_cfg)`
  - Local `config/stage.yaml` should only include true deltas.

## Logging & Services
- Apply logging via `core.logging.configure_logging()`; use v2 categories.
- Cross-phase access must use `core.preprocessing.services.*` or phase APIs.
  - Do not import another phase’s `domain/` or `domain/ops/` from outside services.

## Contracts & Artifacts
- Stamp artifacts via `core.versioning.make_artifact_stamp(schema_name=...)`.
- Register schema names in `core/versioning/schemas.yaml`.
- Add JSON Schemas for artifacts under `core/validation/contracts/artifacts/<phase>/`.
- Add contract tests to validate schema and stamping.

## CI & Gates
- Pre-commit enforces headers, forbids legacy imports and cross-phase domain imports, forbids phase-local tests, and lints policy YAML.
- CI audits block legacy patterns and tracked caches/logs; smoke tests run umbrella CLI basics.

## Commit Style
- Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- No commits directly to `main`.

## Cleanup
- Use `make clean-repo-dry` then `make clean-repo` to remove outputs/logs/caches.

Thanks for contributing!
