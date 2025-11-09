# Heavy Normalization Stage (phase_08_heavy_normalization)

## Purpose
Apply advanced normalization passes (e.g., layout fixes, unicode harmonization) to produce stabilized content for provenance and offsets.

## Workflow (v2)
- API: api.py
- CLI: cli/heavy_normalization_cli_v2.py
- Connectors: connectors/*
- Domain: domain/*
- IO: io/*
- Schemas: schemas/*
- common_files: docs & configs

## Outputs
- cfg['io']['out_doc_path']
- cfg['io']['out_stats_path']
- cfg['io']['out_summary_path']

## Quick Run (v2 CLI)

Use the phase-local v2 CLI to run this stage:

```
python -m backend.Preprocessing.phase_08_heavy_normalization.cli.heavy_normalization_cli_v2 --help
```

## Latest Updates
- 2025-10-05: Retired the external runtime shim; tests and outputs now import the stage-local orchestrator directly.
- 2025-10-04: Modules renamed to satisfy Agent Standard naming rules and CLI defaults sourced from stage configuration.
- 2025-10-04: Added preprocessing_chain integration harness that runs detect_type -> encoding -> readers in one step.

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.

## Quick Run (v2 CLI)

Use the phase-local v2 CLI to run this stage:

```
python -m backend.Preprocessing.phase_08_heavy_normalization.cli.heavy_normalization_cli_v2 --help
```

## Env & Logging
- Configure environment via the repo root `.env.example`.
- Logging is policy-driven under `core/policy/observability/logging/`.
  - Select profile using `MEDFLUX_LOG_PROFILE` (e.g., `dev`, `prod`).
  - v2 CLI supports `--log-level`, `--log-json`, `--log-stderr`.

## Quick Run (Umbrella CLI)

Use the umbrella CLI for consistency:

```
medflux phase-heavy-normalization --inputs path/to/file --output-root ./.artifacts/heavy-normalization
```

## Examples

- Umbrella CLI:
  `\n  medflux phase-heavy_normalization --inputs samples/Sample.txt --output-root ./.artifacts/heavy_normalization\n  `\n- Phase v2 CLI:
  `\n  python -m backend.Preprocessing.phase_08_heavy_normalization.cli.heavy_normalization_cli_v2 --inputs samples/Sample.txt --output-root ./.artifacts/heavy_normalization\n  `\n
