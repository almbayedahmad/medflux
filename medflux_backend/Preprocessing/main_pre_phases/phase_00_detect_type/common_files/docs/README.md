# Detect Type Stage (phase_00_detect_type)

## Purpose
Identify the format and reading strategy for every incoming contract file. The stage inspects PDFs, office documents, plain text, and images, then recommends the appropriate reader mode while emitting stage-compliant outputs.

## Workflow
- Orchestrator: pipeline_workflow/detect_type_pipeline.py
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
make run INPUTS="samples/Sample_pdftext.pdf"
```
Override `INPUTS` with one or more paths (space separated) that should be classified.

## Validation
Run stage checks before committing changes.

```
make validate
```

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.

### change-20251003T202717-update
- What changed: Update stage phase_00_detect_type at 2025-10-03 20:27:17 UTC.
- Why it was needed: Stage assets were modified and documentation must reflect the change.
- Result: Stage and main documentation are synchronised with the latest update.
