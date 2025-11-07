# Preprocessing Integration Tests

This directory now focuses on end-to-end smoke checks that exercise multiple preprocessing stages together.

- `results_test_pipeline_session.py` — runs detect_type → encoding → readers, storing artefacts under ``MEDFLUX_OUTPUT_ROOT` (or <repo>/outputs/preprocessing/pre_smoke_results`)/output_pre_all_phase_results/<run_id>` and mirroring per-stage outputs in the matching stage folders.

Stage-specific sessions and unit tests have been moved back into their respective `main_pre_phases/phase_xx_*` packages to avoid duplication here.
