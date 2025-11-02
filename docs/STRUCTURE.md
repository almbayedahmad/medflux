# Repository Structure

High-level overview of the MedFlux repository layout and purpose of each top-level folder.

- apps/
  - Application entry points (e.g., `web/`).
- assets/
  - Static assets, images and placeholders used in docs or UIs.
- backend/
  - Core Python code for MedFlux (APIs, preprocessing, stages).
- core/
  - Shared libraries and policies (logging, validation, versioning, policy).
  - `core/policy/*` is the canonical home for standards and rules.
- docs/
  - Developer documentation.
  - `docs/legacy/Agent_Standard/` contains archived materials kept for reference.
- local/
  - Local-only files (gitignored) – safe place for developer environment bits.
- logs/
  - Runtime logs (gitignored). Many tools read from here during validation runs.
- outputs/
  - Stage outputs and artifacts (gitignored).
- samples/
  - Example input files used by smoke tests and demos.
- scripts/
  - Small developer helper scripts (e.g., `environment_activate.ps1`).
- shared/
  - Shared schemas/types used across the project.
- tests/
  - Unit and integration tests.
- tools/
  - Developer and CI utilities, organized by function:
    - `tools/versioning`: bump/verify version
    - `tools/schema`: schema bump/docs/verification
    - `tools/validation`: phase/artifact validation + reports
    - `tools/logs`: log helpers and validation
    - `tools/monitoring`: local observability stack (Prometheus, Grafana, Loki, etc.)
    - `tools/ci`: CI-only checks

Top-level files
- README.md – project overview and quick start
- CHANGELOG.md – release notes
- pyproject.toml – build and packaging metadata
- Makefile – optional shortcuts for common tasks
- .pre-commit-config.yaml – code quality hooks
- .github/ – GitHub Actions workflows and reusable actions

Notes
- Run scripts from repo root so relative paths resolve (e.g., `PYTHONPATH=.`)
- See `tools/TOOLS.md` for commands and the tools catalog.
