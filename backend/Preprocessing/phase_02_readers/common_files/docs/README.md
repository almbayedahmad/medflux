# Readers Stage (phase_02_readers)

## Purpose
Orchestrate document ingestion by dispatching native, OCR, and table extraction flows to produce structured metadata for downstream preprocessing steps.

## Workflow (v2)
- API: api.py
- CLI: cli/readers_cli_v2.py
- Connectors: connectors/* (config, upstream, metadata)
- Domain: domain/*
- IO: io/*
- Schemas: schemas/*

This stage uses the v2 layout and APIs exclusively. Legacy paths are retired.

## Outputs
- cfg['io']['out_doc_path']
- cfg['io']['out_stats_path']
- cfg['io']['out_summary_path']

## How to Run (v2 CLI)
```
python -m backend.Preprocessing.phase_02_readers.cli.readers_cli_v2 --help
```

## Quick Run (Umbrella CLI)

Alternatively, invoke the readers phase via the umbrella CLI:

```
medflux phase-readers --inputs path/to/file.pdf --output-root ./.artifacts/readers
```

Or run the full chain:

```
medflux chain-run --inputs path/to/file.txt --output-root ./.artifacts/chain --include-docs
```

## Examples

- Umbrella CLI (single file):
  ```
  medflux phase-readers --inputs samples/Sample.pdf --output-root ./.artifacts/readers
  ```
- Phase v2 CLI:
  ```
  python -m backend.Preprocessing.phase_02_readers.cli.readers_cli_v2 --inputs samples/Sample.pdf --output-root ./.artifacts/readers
  ```

## Env & Logging
- Use the root `.env.example` for environment variables.
- Logging is policy-driven under `core/policy/observability/logging/`.
  - Set `MEDFLUX_LOG_PROFILE=dev` (or `prod`) to switch profiles.
  - CLI flags `--log-level`, `--log-json`, `--log-stderr` are available (umbrella + v2 CLIs).

## Latest Updates
- 2025-10-05: Retired the external runtime shim; tests and outputs now import the stage-local orchestrator directly.
- 2025-10-04: Modules renamed to satisfy Agent Standard naming rules and CLI defaults sourced from stage configuration.
- 2025-10-04: Added preprocessing_chain integration harness that runs detect_type -> encoding -> readers in one step.

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.
