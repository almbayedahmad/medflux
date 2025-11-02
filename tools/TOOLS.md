# MedFlux Tools Overview

This repository groups developer and CI utilities under `tools/` by function. Run commands from the repo root unless noted.

## Structure

- versioning
  - `bump_version.py` – bump `core/versioning/VERSION` (major/minor/patch)
  - `verify_version.py` – ensure runtime version matches file version
- schema
  - `generate_schema_docs.py` – build `core/validation/SCHEMAS.md` (use `--check` in CI)
  - `schema_bump.py` – bump a contract in `core/versioning/schemas.yaml` and write migration entry
  - `verify_schema_version.py` – check declared vs runtime schema version
  - `verify_migrations.py` – enforce strictly increasing migration numbering
  - `validate_schemas.py` – validate all JSON Schemas compile vs Draft 2020-12 metaschema
- validation
  - `validate_phase.py` – validate inputs/outputs for a phase against schemas
  - `validate_artifacts.py` – validate saved artifacts against artifact schemas or fallback contract
  - `validation_report.py` – consolidated report across phases, logs, and artifacts
  - `validate_schemas.py` – (same as schema/validate_schemas via wrapper)
- logs
  - `link_latest.py`, `query.py`, `tail.py`, `validate_records.py` – log helpers
- monitoring
  - Docker Compose stack (Prometheus, Grafana, Alertmanager, Tempo, Loki, Promtail)
  - See `tools/monitoring/README.md` for setup and usage
- ci
  - `verify_commit_semantics_vs_version.py` – commit semantics align with VERSION
  - `verify_changelog_for_version_bump.py` – changelog includes bumped version
  - `verify_stamp_coverage.py` – outputs contain `versioning.app_version`

## Common commands

- Versioning
  - `python tools/versioning/bump_version.py patch`
  - `python tools/versioning/verify_version.py`
- Schema
  - `python tools/schema/generate_schema_docs.py --check`
  - `python tools/schema/schema_bump.py stage_contract minor`
  - `python tools/schema/verify_schema_version.py`
  - `python tools/schema/verify_migrations.py`
  - `python tools/validation/validate_schemas.py`
- Validation
  - `python tools/validation/validate_phase.py phase_00_detect_type output sample.json --log-json --explain`
  - `python tools/validation/validate_artifacts.py --auto outputs/detect_type_unified_document.json`
  - `python tools/validation/validation_report.py --phase-output phase_00_detect_type:sample.json --logs-root logs --out-md report.md`
- Logs
  - `python tools/logs/validate_records.py --root logs --glob "**/*.jsonl" --min-context 0.95`
- Monitoring
  - `docker compose -f tools/monitoring/docker-compose.yml up -d`
  - `pwsh tools/monitoring/monitoring.ps1 up`

## Notes

- Python: scripts target Python 3.11+ (3.12 for dev where possible).
- Working dir: run from repository root so relative paths resolve.
- Env vars (selected):
  - `PYTHONPATH=.` – for running local modules in CI or ad‑hoc scripts
  - `MEDFLUX_LOG_FORMAT=json` – JSON logs for validation scripts
  - `MFLUX_SCHEMA_ROOT` – override schema root for `validate_phase.py`
- Windows monitoring: install `windows_exporter` (port 9182) for Windows dashboards.
- Linux-only exporters (node-exporter/cAdvisor) are under a compose profile `linux`.
