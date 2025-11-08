# Changelog - MedFlux

All notable changes to this project will be documented here.

## [v0.1.0] - 2025-10-26
- Initial internal versioning structure implemented.

## [Unreleased]

- refactor(preprocessing):
  - Move `backend/Preprocessing/main_pre_phases/phase_01_encoding` to
    `backend/Preprocessing/phase_01_encoding`.
  - Move `backend/Preprocessing/main_pre_phases/phase_02_readers` to
    `backend/Preprocessing/phase_02_readers`.
  - Update imports, docs, and CI references accordingly. No behavioral changes.

- chore(policy): remove outdated `core/policy/architecture/tree_structure_standard.yaml`
  as the repository structure has been refactored; references updated. No
  runtime behavior impact.

## [v0.1.1] - 2025-11-02
- ci: add schema compatibility guard and improve gates (project 70%, Codecov patch 80%)
- test: add logging + versioning unit tests (redaction, formatter, context, schema)
- docs: add architecture overview, validation playbook, logs guide
- chore: remove legacy folders (medflux_backend, Agent_Standard) and tracked logs
- ci: consolidate workflows and validation steps
