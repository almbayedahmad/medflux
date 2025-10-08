# Encoding Stage (phase_01_encoding)

## Purpose
Detect character encodings for incoming documents and optionally normalize them to UTF-8 with consistent newline handling.

## Workflow
- Orchestrator: pipeline_workflow/encoding_pipeline.py
- Connectors: connecters/*
- Core processors: core_processors/*
- Schemas: schemas/*
- Helpers: internal_helpers/*
- Outputs: outputs/*

## Outputs
- cfg['io']['out_doc_path'] (unified_document)
- cfg['io']['out_stats_path'] (stage_stats)

## How to Run
```
make run INPUTS="samples/Sample.txt" NORMALIZE=1
```
`NORMALIZE=1` converts inputs to UTF-8; omit it to only detect encodings.

## Validation
```
make validate
```

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the placeholders after review.

### change-20251003T205324-update
- What changed: Update stage phase_01_encoding at 2025-10-03 20:53:24 UTC.
- Why it was needed: Stage assets were modified and documentation must reflect the change.
- Result: Stage and main documentation are synchronised with the latest update.
