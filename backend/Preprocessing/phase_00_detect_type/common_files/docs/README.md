# Detect Type Stage (phase_00_detect_type)

## Purpose
Identify the format and reading strategy for every incoming contract file. The stage inspects PDFs, office documents, plain text, and images, then recommends the appropriate reader mode while emitting stage-compliant outputs.

## Workflow (v2)
- API: api.py
- CLI: cli/detect_type_cli_v2.py
- Connectors: connectors/*
- Domain: domain/*
- IO: io/*
- Schemas: schemas/*

This stage uses the v2 layout and APIs exclusively. Legacy paths are retired.

## Outputs
- cfg['io']['out_doc_path'] (unified_document)
- cfg['io']['out_stats_path'] (stage_stats)

## How to Run (v2 CLI)
```
python -m backend.Preprocessing.phase_00_detect_type.cli.detect_type_cli_v2 --help
```
Provide one or more input paths (space separated) to classify.

## Quick Run (Umbrella CLI)

Use the top-level CLI for a unified experience:

```
medflux phase-detect --inputs path/to/file1 path/to/file2 --output-root ./.artifacts/detect
```

## Examples

- Umbrella CLI (single file):
  ```
  medflux phase-detect --inputs samples/Sample.txt --output-root ./.artifacts/detect
  ```
- Phase v2 CLI:
  ```
  python -m backend.Preprocessing.phase_00_detect_type.cli.detect_type_cli_v2 --inputs samples/Sample.txt --output-root ./.artifacts/detect
  ```

## Env & Logging
- Environment: configure variables in the root `.env.example` (copy to `.env`).
- Logging: governed by policy under `core/policy/observability/logging/`.
  - Select profile via `MEDFLUX_LOG_PROFILE` (e.g., `dev`, `prod`).
  - CLI flags `--log-level`, `--log-json`, `--log-stderr` are available (umbrella + v2 CLIs).

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.

### change-20251003T202717-update
- What changed: Update stage phase_00_detect_type at 2025-10-03 20:27:17 UTC.
- Why it was needed: Stage assets were modified and documentation must reflect the change.
- Result: Stage and main documentation are synchronised with the latest update.
