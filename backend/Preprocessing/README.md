# Preprocessing Pipeline

This directory contains the preprocessing pipeline for the medflux backend system.

## Structure

```
Preprocessing/
├── main_pre_standards/          # Scaffolding helpers (phase generator); policies live in core/policy/
├── main_pre_phases/             # Individual processing phases
├── main_pre_helpers/            # Cross-phase utility functions
├── main_pre_schemas/            # Shared data schemas
├── main_pre_config/             # Pipeline configuration
├── main_pre_pipeline/           # Main pipeline orchestration
├── main_pre_samples/            # Sample files for testing
└── main_pre_tests/              # Integration tests
```

> Central governance docs live in `core/policy`; use the helpers under `main_pre_standards/` only for scaffolding automation.

## Phases

The preprocessing pipeline consists of 11 phases:

- **phase_00_detect_type**: File type detection
- **phase_01_encoding**: Text encoding normalization
- **phase_02_readers**: Document reading and OCR
- **phase_03_merge**: Content merging
- **phase_04_cleaning**: Content cleaning
- **phase_05_light_normalization**: Light text normalization
- **phase_06_segmentation**: Text segmentation
- **phase_07_table_extraction**: Table extraction
- **phase_08_heavy_normalization**: Heavy text normalization
- **phase_09_provenance**: Provenance tracking
- **phase_10_offsets**: Offset calculation

## Recent Changes (v2.0.0)

**Major Structural Update**: The preprocessing pipeline has been restructured with a minimal phase approach:
- **Centralized Standards**: All project-wide policies moved to `core/policy/`
- **Eliminated Templates**: Removed ~110 template files with placeholders
- **Single Source of Truth**: Documentation duplication eliminated
- **Automated Creation**: Phase generator script replaces manual setup

See [CHANGELOG.md](./CHANGELOG.md) for detailed migration notes.

## Standards and Development

### Creating New Phases

Use the phase generator script to create new phases:

```bash
python main_pre_standards/development/phase_generator.py 11 validation
```

### Development Standards

- Follow guidelines in `core/policy/developer_setup/development_checklist.md`
- Use phase creation guide in `core/policy/developer_setup/phase_scaffolding_guide.md`
- Adhere to documentation conventions in `core/policy/documentation/docs_conventions.yaml`

### Git Workflow

- Follow commit conventions in `core/policy/git/commit_conventions.md`
- Use git rules in `core/policy/git/git_rules.md`

## Phase Structure

Each phase follows a minimal, standardized structure:

```
phase_XX_stage/
├── __init__.py
├── config/                    # Phase-specific configuration
├── core_functions/            # Core processing logic
├── connecters/                # Cross-phase communication
├── schemas/                   # Data type definitions
├── outputs/                   # Output generation
├── internal_helpers/          # Phase-specific utilities
├── pipeline_workflow/         # Pipeline orchestration
├── tests/                     # Unit tests
└── common_files/             # Essential phase files
    ├── docs/
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

## Running the Pipeline

### Individual Phase

```bash
cd phase_XX_stage
make run INPUTS="samples/sample_file.txt"
```

### Full Pipeline

```bash
python main_pre_pipeline/preprocessing_chain.py
```

Outputs default to `MEDFLUX_OUTPUT_ROOT` (or `<repo>/outputs/preprocessing`). Override with `--output-root` when running smoke tests to keep artifacts out of the repo.

## Testing

### Unit Tests

```bash
python -m pytest main_pre_phases/phase_XX_stage/tests/ -v
```

### Integration Tests

```bash
python -m pytest main_pre_tests/ -v
```

## Configuration

- Pipeline configuration: `main_pre_config/pipeline_config.yaml`
- Validation rules: `main_pre_config/validation_rules.yaml`
- Logging configuration: `main_pre_config/logging_config.yaml`

## Samples

Test files are available in `main_pre_samples/`:
- PDF samples
- DOCX samples
- Image samples
- Text samples
- Table samples

## Migration Notes

- Template files with placeholders have been removed
- Project-wide policies moved to `core/policy/`
- Phase-specific files remain in each phase's `common_files/`
- Phase generator script replaces manual template copying

## Support

For questions about the preprocessing pipeline:
- Check the phase creation guide in `core/policy/developer_setup/phase_scaffolding_guide.md`
- Review existing phase examples
- Use the phase generator script
- Contact the development team
