Title
- refactor(preprocessing): move phases 01–10 to backend/Preprocessing root and update imports/docs/CI

Summary
- Refactor the preprocessing package structure by moving phases 01–10 from `backend/Preprocessing/main_pre_phases` to the root under `backend/Preprocessing/phase_XX_*`, aligning with `phase_00_detect_type`. Updated all imports, orchestration code, tests, CI and docs accordingly. No functional behavior changes in the phases; only import paths and documentation were altered. All project gates (pre-commit, pytest, yamllint for policy dir) pass locally.

Changes
- Move phases to root
  - `phase_01_encoding` … `phase_10_offsets` moved under `backend/Preprocessing/`
  - Removed legacy `backend/Preprocessing/main_pre_phases` directory
- Update imports and orchestrators
  - `core/preprocessing/pipeline/preprocessing_chain.py` updated to import from new paths
  - `core/preprocessing/pipeline/detect_and_read.py` updated (readers CLI)
  - Tests updated where importing readers/encoding internals
  - CI workflow step updated for encoding CLI path
- Docs and configs
  - `backend/Preprocessing/README.md` structure block now lists all root phases
  - `CHANGELOG.md` and `backend/Preprocessing/CHANGELOG.md` entries added
  - Added repo `.yamllint` with 2-space indentation and sequence rules
  - Normalized `core/policy/observability/logging/logging_config.yaml` formatting
  - Removed outdated `core/policy/architecture/tree_structure_standard.yaml` and references

Testing
- Environment
  - Installed `requirements.txt` and `requirements-dev.txt`
- Validation
  - `pre-commit run --all-files` → pass
  - `yamllint core/policy` → pass (no errors; one benign comments-indentation warning)
  - `pytest -q` → all tests pass (deprecation warnings only)

Risk/Compatibility
- Import path change only; behavior of phases unchanged
- External consumers must update imports from `backend.Preprocessing.main_pre_phases.phase_XX_*` to `backend.Preprocessing.phase_XX_*`
- No data/schema changes introduced by this refactor

Migration Notes
- Legacy `main_pre_phases` removed; references in changelog remain for history
- Structure documentation updated to reflect new layout

Checklist
- [x] Ran `pre-commit run --all-files`
- [x] Ran `pytest -q` (all green)
- [x] `yamllint core/policy` (no errors)
- [x] Updated README/CHANGELOG where applicable
- [x] No secrets/PII introduced; logs follow event/redaction policies

Links
- Branch: `fix/python-setup-action`
- Compare/PR: https://github.com/almbayedahmad/medflux/compare/fix/python-setup-action?expand=1
