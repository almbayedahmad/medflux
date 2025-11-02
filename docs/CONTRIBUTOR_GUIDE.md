# Contributor Guide

Welcome! This guide links the most relevant docs and checklists to contribute effectively to MedFlux.

## Start Here
- Repo Overview: docs/STRUCTURE.md
- Architecture Overview: docs/architecture_overview.md
- Validation Playbook: docs/validation_playbook.md
- Logging Guide: core/logging/README.md
- Monitoring Stack: tools/monitoring/README.md
- Branch Protection Checks: docs/BRANCH_PROTECTION.md

## Development Workflow
1) Create a short-lived branch (e.g., `feat/x`, `fix/y`).
2) Write tests first, or alongside changes.
3) Run pre-commit locally: `pre-commit run --all-files`.
4) Run tests with coverage:

   ```powershell
   pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=term
   ```

   - Project coverage ≥ 80% required; patch coverage ≥ 80% (Codecov).
   - See `.coveragerc` for measured scope (focus on `core` and `backend/api`).
5) Open a PR to `main` with a clear title and summary (see template).

## Versioning & Releases
- Version file: `core/versioning/VERSION`.
- Schema compatibility guard (CI) blocks breaking changes unless MAJOR increases.
- Release options:
  - Bump VERSION and tag `vX.Y.Z`, push.
  - Or run the manual Release workflow in GitHub Actions.

## Logging & Observability
- Env toggles: `MEDFLUX_LOG_JSON`, `MEDFLUX_LOG_TO_STDERR`, `MEDFLUX_LOG_FILE`, `MEDFLUX_LOG_DAILY`, `MEDFLUX_LOG_ROOT`.
- Prod profile (`MEDFLUX_LOG_PROFILE=prod`) enables JSON console, queue handler, and supports daily rotation.
- Configure log destinations per-run: `configure_log_destination(run_id, phase, flow=None)`.
- Monitoring stack at `tools/monitoring` (Prometheus, Grafana, Loki, Tempo).
- Email alerts are disabled by default (blackhole receiver). See tools/monitoring/README.md to re-enable.

## Required Status Checks (suggested)
- Lint (pre-commit)
- Tests (matrix)
- Schema & Docs
- Policy & Version Checks
- Package Parity
- Smoke
- Integration
- CodeQL
- Commitlint

See docs/BRANCH_PROTECTION.md for job names and how to enable in GitHub.

## Conventional Commits
- `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`
- Commitlint runs in CI.

## Helpful Tools
- `tools/schema/…`: schema validation, docs generation, version checks
- `tools/validation/…`: phase/artifact validation & reports
- `tools/logs/…`: JSONL log validators and helpers
- `tools/monitoring/…`: stack orchestration, sample traffic, health checks
