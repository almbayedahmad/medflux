# Preprocessing Integration Tests

This directory contains the end-to-end smoke checks that exercise multiple preprocessing stages together.

- `test_pipeline_session.py` – runs detect_type → encoding → readers, storing artefacts under ``MEDFLUX_OUTPUT_ROOT` (or `<repo>/outputs/preprocessing/pre_smoke_results`)/output_pre_all_phase_results/<run_id>` and mirroring per-stage outputs in the matching stage folders.

Stage-specific sessions and unit tests live alongside their respective `phase_XX_*` packages; only cross-phase integration tests should reside here.
