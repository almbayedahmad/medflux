# {{ StageName }} Stage (phase_{{ phase_number }}_{{ stage_name }})

## Purpose
Provide a concise description of what this stage accomplishes.

## Workflow
- Orchestrator: pipeline_workflow/{{ stage_name }}_pipeline.py
- Connectors: connecters/*
- Core processors: core_processors/*
- Schemas: schemas/*
- Helpers: internal_helpers/*
- Outputs: outputs/*

## Outputs
- cfg['io']['out_doc_path']
- cfg['io']['out_stats_path']

## How to Run
```
make run
```

## Validation
Run stage checks before committing changes.

```
make validate STAGE={{ stage_dir_name }}
```

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.
