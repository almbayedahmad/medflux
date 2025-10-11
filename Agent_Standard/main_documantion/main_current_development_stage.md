phase_02_readers - active as of 2025-10-04 12:26:00 UTC (in progress)

Summary:
- Added a preprocessing_chain CLI that runs detect_type -> encoding -> readers and captures per-stage outputs.
- Seeded lightweight smoke fixtures (text, image, PDF) and updated the smoke script to exercise the new chain.
- Bootstrapped stage-local runtime modules (readers_options/settings/logging/language, execution wrappers, doc-meta wrapper) and pointed tests/docs at them.

Next Steps:
- Migrate the remaining runtime orchestrator logic into the stage-local package and retire medflux_backend/readers_runtime.
- Update preprocessing docs and tests once the full runtime relocation is complete.
