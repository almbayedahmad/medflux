# Encoding Stage (phase_01_encoding)

## Purpose
Detect character encodings for incoming documents and optionally normalize them to UTF-8 with consistent newline handling.

## Workflow (v2)
- API: api.py
- CLI: cli/encoding_cli_v2.py
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
python -m backend.Preprocessing.phase_01_encoding.cli.encoding_cli_v2 --help
```
Use `--normalize` to convert inputs to UTF-8; omit it to only detect encodings.

## Validation
```
make validate
```

## Quick Run (Umbrella CLI)

Use the top-level CLI to run encoding with consistent options:

```
medflux phase-encoding --inputs path/to/file.txt --normalize --output-root ./.artifacts/encoding
```

## Examples

- Umbrella CLI (normalize example):
  ```
  medflux phase-encoding --inputs samples/Sample.txt --normalize --output-root ./.artifacts/encoding
  ```
- Phase v2 CLI:
  ```
  python -m backend.Preprocessing.phase_01_encoding.cli.encoding_cli_v2 --inputs samples/Sample.txt --output-root ./.artifacts/encoding --normalize
  ```

## Env & Logging
- Environment: use the root `.env.example` as the single source; copy to `.env` if needed.
- Logging policy: `core/policy/observability/logging/`.
  - Select profile with `MEDFLUX_LOG_PROFILE` (e.g., `dev`, `prod`).
  - CLI flags `--log-level`, `--log-json`, `--log-stderr` are available (umbrella + v2 CLIs).

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the placeholders after review.

### change-20251003T205324-update
- What changed: Update stage phase_01_encoding at 2025-10-03 20:53:24 UTC.
- Why it was needed: Stage assets were modified and documentation must reflect the change.
- Result: Stage and main documentation are synchronised with the latest update.
