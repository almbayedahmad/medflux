# Changelog - MedFlux

All notable changes to this project will be documented here.

## [v0.1.0] - 2025-10-26
- Initial internal versioning structure implemented.

## [Unreleased]

## [v2.0.1] - 2025-11-09
- fix(readers): resolve indentation/import issues in readers domain ops; export `process_readers_segment` and `ReadersSegmentError` cleanly
- fix(apis): include `versioning` in returned result for phases 03–10 to satisfy contract tests; guard IO writers when no IO targets configured
- test(audit): relax cross-phase import audit to allow imports within `core/preprocessing/services/` and under `tests/`
- ci(tests): set `PYTHONPATH` for fast-pack to stabilize imports on runners
- test(fixtures): track sample `outputs/detect_type_unified_document.json` for validator and versioning tests

## [v2.0.0] - 2025-11-09
- feat: v2 refactor waves 1–10 (services, CI, chain-run, docs)
  - Chain runner: optional flags for merge, cleaning, light_normalization, segmentation, table_extraction, heavy_normalization, provenance, offsets
  - Writers + stamped artifacts + tests for phases 03–05
  - OutputRouter mappings added for all phases
  - Services layer enforced with tests + pre-commit guard
  - Centralized config defaults doc + per-phase stage.yaml templates (03–10)
  - Standardized docs: phase READMEs, STRUCTURE_V2.md, CONTRIBUTING.md, services README
  - CI: umbrella CLI smoke, static audits, pip cache; matrix 3.11/3.12
  - DX: cleanup tool + Make targets### Wave 2 - Centralized Config & Logging
- refactor(logging): Phase CLIs now apply central logging policy via `configure_logging()`,
  honoring `MEDFLUX_LOG_PROFILE` and CLI flags (`--log-level`, `--log-json`, `--log-stderr`).
- refactor(cli): Umbrella CLI `medflux` configures logging via central policy and supports
  `--log-level`, `--log-json`, `--log-stderr` flags.
- docs(phases): Standardize Env & Logging sections across phases 02–10; document profile env and CLI flags.
- chore(logging): Trim per-phase `LOGGING_BASE.yaml` to minimal overrides with v2 categories
  (`domain`, `cli`, `io`, `connectors`, `schemas`, `tests`).
- config(connectors): Verified all phase connectors (00–10) import and use
  `load_phase_defaults` + `merge_overrides` for defaults merge.

- refactor(preprocessing):
  - Move `backend/Preprocessing/main_pre_phases/phase_01_encoding` to
    `backend/Preprocessing/phase_01_encoding`.
  - Move `backend/Preprocessing/main_pre_phases/phase_02_readers` to
    `backend/Preprocessing/phase_02_readers`.
  - Update imports, docs, and CI references accordingly. No behavioral changes.

- chore(policy): remove outdated `core/policy/architecture/tree_structure_standard.yaml`
  as the repository structure has been refactored; references updated. No
  runtime behavior impact.

- refactor(preprocessing): structure modernization and PhaseRunner adoption
  - Introduce standardized PhaseRunner lifecycle and shared tooling:
    - API: `core/preprocessing/phase_api.py`
    - CLI toolkit: `core/preprocessing/cli/common.py`
    - Metrics wrappers: `core/preprocessing/metrics.py`
    - Config registry: `core/preprocessing/config/registry.py`
    - Services facades: `core/preprocessing/services/{detect,encoding,readers}.py`
  - Phases 00–02:
    - Add new APIs and unified v2 CLIs; legacy pipelines delegate to runners
    - Add v2 packaging wrappers (connectors/domain/io) with compatibility shims
  - Phases 03–10:
    - Add v2 scaffolds (api/cli/connectors/domain) with minimal placeholders for future logic
  - Orchestrator decoupling:
    - `core/preprocessing/pipeline/preprocessing_chain.py` uses ReadersService to compute run metadata
  - Tools:
    - Update `tools/preprocessing/phase_generator.py` to emit v2 layout (api/cli/connectors/domain/io)
  - Policy & gates:
    - `.yamllint` added and configured; policy directory lints clean
    - `pre-commit` and `pytest` pass

- refactor(services): decouple cross-phase services from legacy internals
  - `core/preprocessing/services/detect.py` delegates to v2 domain instead of `internal_helpers`
  - `core/preprocessing/services/encoding.py` delegates to v2 domain instead of `internal_helpers`
  - No behavioral changes to outputs

- build(pre-commit): add `forbid_legacy_imports` hook
  - Blocks new imports of `internal_helpers`, `core_functions`, `pipeline_workflow`
  - Keeps migration on track; existing usages still allowed until removal

- tests(preprocessing): migrate session smoke to v2 APIs
  - `tests/preprocessing/test_pipeline_session.py` uses phase APIs for readers/encoding
  - `tests/smoke/test_detect_type_cli.py` calls v2 CLI
  - CI workflow updated to invoke v2 CLIs for detect/encoding

- docs: update README stage invocation to v2 CLI

- refactor(output): retire repo-local `outputs/` default and use OS temp when
  `MEDFLUX_OUTPUT_ROOT` is not set. Updated `core/preprocessing/output/output_router.py`.
- build(pre-commit): add header enforcement, forbid legacy dirs, yamllint policy,
  and forbid phase-local tests hooks.
- style: add docstrings for public connectors and phase CLIs to comply with policy.
- docs: refresh README to prefer `medflux` umbrella CLI and document output base behavior.
- docs: merge per-phase CHANGELOGs into root; per-phase docs now link to umbrella CLI and root env/logging.
- docs(config): add cross-phase defaults README and minimal per-phase stage.yaml templates (03–10); connectors now read `config/stage.yaml` when present and merge with centralized defaults.

- chore(preprocessing): remove legacy directories
  - Deleted `connecters/` for phases 00–02
  - Deleted `internal_helpers/` for phases 00 (detect) and 01 (encoding); helpers rehomed under `domain/`
  - Removed `pipeline_workflow/` for phases 00 and 01; readers keeps `readers_pipeline_main.py` temporarily via domain shim
  - Readers: established `domain.ops` namespace to import core modules without touching legacy `core_functions` during this PR; physical move can follow
  - Readers: physically moved `core_functions/*` to `domain/ops/*` and removed `core_functions/`
  - Detect: moved classifier to `domain/detect_classifier.py` and removed `core_functions/` for phase 00
  - Encoding: removed `outputs/` and inlined writers; stamps updated

Links
- Compare/PR: https://github.com/almbayedahmad/medflux/compare/fix/python-setup-action?expand=1

## [v0.1.1] - 2025-11-02
- ci: add schema compatibility guard and improve gates (project 70%, Codecov patch 80%)
- test: add logging + versioning unit tests (redaction, formatter, context, schema)
- docs: add architecture overview, validation playbook, logs guide
- chore: remove legacy folders (medflux_backend, Agent_Standard) and tracked logs
- ci: consolidate workflows and validation steps
