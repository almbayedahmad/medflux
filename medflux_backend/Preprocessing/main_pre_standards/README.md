# Main Preprocessing Standards

This directory contains project-wide standards, policies, and templates for the preprocessing pipeline phases.

## Directory Structure

```
main_pre_standards/
├── development/
│   ├── PHASE_CREATION_GUIDE.md    # Guide for creating new phases
│   ├── DEVELOPMENT_CHECKLIST.md   # Quality checklist for development
│   └── phase_generator.py          # Automated phase creation script
├── documentation/
│   ├── DOCS_CONVENTIONS.yaml      # Documentation standards
│   ├── LANGUAGE_POLICY.yaml       # Language and localization policy
│   └── NAMING_STANDARDS.md        # File and function naming conventions
├── git/
│   ├── COMMIT_CONVENTIONS.md      # Git commit message standards
│   └── GIT_RULES.md               # Git workflow rules
├── policies/
│   ├── STAGE_CONTRACT_TEMPLATE.yaml    # Stage contract template
│   ├── VALIDATION_RULES_TEMPLATE.yaml  # Validation rules template
│   └── KPIS_TEMPLATE.yaml              # Key performance indicators template
└── versioning/
    ├── SCHEMA_VERSIONING.md        # Schema versioning policy
    └── VERSIONING_POLICY.md        # General versioning policy
```

## Usage

### Creating a New Phase

Use the phase generator script to create a new phase with minimal structure:

```bash
python main_pre_standards/development/phase_generator.py 03 segment
```

This will create `phase_03_segment` with all required directories and files.

### Development Standards

- Follow the guidelines in `development/DEVELOPMENT_CHECKLIST.md`
- Use the phase creation guide in `development/PHASE_CREATION_GUIDE.md`
- Adhere to documentation conventions in `documentation/DOCS_CONVENTIONS.yaml`
- Follow naming standards in `documentation/NAMING_STANDARDS.md`

### Git Workflow

- Follow commit conventions in `git/COMMIT_CONVENTIONS.md`
- Use git rules in `git/GIT_RULES.md`
- Use the commit message template from phase `common_files/git/.gitmessage`

### Configuration Templates

- Use policy templates from `policies/` directory
- Customize templates for phase-specific needs
- Follow versioning policies in `versioning/` directory

## Benefits

1. **Centralized Standards**: All project-wide policies in one location
2. **Consistent Structure**: All phases follow the same minimal structure
3. **Reduced Duplication**: No more duplicate template files across phases
4. **Automated Creation**: Phase generator replaces manual template copying
5. **Easy Maintenance**: Update standards once, applies everywhere

## Phase Structure

Each phase now contains only essential files with **single source of truth** for documentation:

```
phase_XX_stage/
├── __init__.py
├── config/
├── core_functions/
├── connecters/
├── schemas/
├── outputs/
├── internal_helpers/
├── pipeline_workflow/
├── tests/
└── common_files/
    ├── docs/                  # Single source of truth for documentation
    │   ├── README.md
    │   └── CHANGELOG.md
    ├── git/
    │   ├── Makefile
    │   └── .gitmessage
    └── configs/
        ├── ENV.sample
        ├── LOGGING_BASE.yaml
        └── SETTINGS_BASE.yaml
```

**Note**: Duplicate `docs/` directories have been eliminated. All documentation is now in `common_files/docs/` only.

## Migration Notes

- Template files with placeholders have been removed from all phases
- Project-wide policies moved to this directory
- **Duplicate `docs/` directories eliminated** - single source of truth in `common_files/docs/`
- Phase-specific files remain in each phase's `common_files/` directory
- Phase generator script replaces manual INIT_PHASE.md process

## Support

For questions about standards or phase creation:
- Check the phase creation guide
- Use the phase generator script
- Review existing phase examples
- Contact the development team
