# Changelog

All notable changes to the Preprocessing Pipeline will be documented in this file.

## [2.0.0] - 2025-01-08

### Major Structural Changes

#### Added
- **main_pre_standards/**: New centralized standards directory
  - `development/`: Phase creation guide, development checklist, phase generator script
  - `documentation/`: Project-wide documentation standards and language policies
  - `git/`: Git workflow rules and commit conventions
  - `policies/`: Stage contracts, validation rules, and KPIs
  - `versioning/`: Schema versioning and versioning policies
- **Phase Generator Script**: Automated phase creation (`phase_generator.py`)
- **Centralized Standards**: All project-wide policies in single location

#### Changed
- **Phase Structure**: Implemented minimal phase structure
  - Renamed `core_processors/` to `core_functions/` across all phases
  - Renamed `config_profiles/` to `config/` in phase_02_readers
  - Standardized naming conventions for all files
- **Documentation**: Single source of truth for phase documentation
  - Eliminated duplicate `docs/` directories
  - All documentation now in `common_files/docs/` only

#### Removed
- **Template Files**: Removed ~110 template files with placeholders
  - `INIT_PHASE.md`, `PHASE_CHECKLIST.md`, `LANGUAGE_POLICY.yaml`
  - `DOCS_CONVENTIONS.yaml`, `ISSUE_TEMPLATE.md`, `PULL_REQUEST_TEMPLATE.md`
  - `COMMIT_CONVENTIONS.md`, `GIT_RULES.md`, `CODEOWNERS`
  - `KPIS.yaml`, `STAGE_CONTRACT.yaml`, `VALIDATION_RULES.yaml`
  - `AGENT_INSTRUCTIONS.md`, `SCHEMA_VERSIONING.md`, `VERSIONING_POLICY.md`
- **Documentation Duplication**: Eliminated duplicate `docs/` directories
- **Maintenance Burden**: Reduced from 11 phases × multiple templates to centralized standards

### Benefits
- **Reduced Duplication**: Project-wide policies in one location
- **Cleaner Structure**: Only essential files per phase
- **Easier Maintenance**: Update once, applies everywhere
- **Less Confusion**: Clear separation of concerns
- **Automated Creation**: Script replaces manual template copying
- **Single Source of Truth**: No more duplicate documentation

### Migration Notes
- Template files with placeholders have been removed
- Project-wide policies moved to `main_pre_standards/`
- Duplicate `docs/` directories eliminated
- Phase-specific files remain in each phase's `common_files/`
- Phase generator script replaces manual INIT_PHASE.md process

## [1.0.0] - Previous Version
- Initial preprocessing pipeline implementation
- Individual phase structures with template files
- Manual phase creation process
