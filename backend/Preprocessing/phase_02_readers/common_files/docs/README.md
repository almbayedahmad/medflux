# Readers Stage (phase_02_readers)

## Purpose
Orchestrate document ingestion by dispatching native, OCR, and table extraction flows to produce structured metadata for downstream preprocessing steps.

## Workflow
- Orchestrator: pipeline_workflow/readers_pipeline.py
- Connectors: connecters/*
- Core processors: core_processors/*
- Schemas: schemas/*
- Internal helpers: internal_helpers/ (runtime models/options, language/logging, execution helpers)
- Outputs: outputs/ (doc builders, documents/)

## Outputs
- cfg['io']['out_doc_path']
- cfg['io']['out_stats_path']
- cfg['io']['out_summary_path']

## How to Run
```
python -m backend.Preprocessing.phase_02_readers.pipeline_workflow.readers_cli --out outputs/phase_02_readers samples/sample_text_smoke.txt
```

Run the detect_type -> encoding -> readers chain (smoke defaults write to ``MEDFLUX_OUTPUT_ROOT` (or <repo>/outputs/preprocessing/pre_smoke_results`)`):
```
python -m core.preprocessing.pipeline.preprocessing_chain \
  --inputs samples/sample_text_smoke.txt samples/sample_pdf_smoke.pdf \
  --include-docs
```

## Latest Updates
- 2025-10-05: Retired the external runtime shim; tests and outputs now import the stage-local orchestrator directly.
- 2025-10-04: Modules renamed to satisfy Agent Standard naming rules and CLI defaults sourced from stage configuration.
- 2025-10-04: Added preprocessing_chain integration harness that runs detect_type -> encoding -> readers in one step.

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.
