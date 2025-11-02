# Naming Standards

This document defines the standardized naming conventions for the preprocessing pipeline.

## File Naming Rules

### Phase Layer Files

#### Core Functions
- **Pattern**: `<stage>_core_<functionality>.py`
- **Examples**:
  - `readers_core_pdf.py`
  - `readers_core_ocr.py`
  - `detect_type_core_classifier.py`
  - `encoding_core_normalizer.py`

#### Pipeline Workflow
- **Pattern**: `<stage>_pipeline.py`
- **Examples**:
  - `readers_pipeline.py`
  - `detect_type_pipeline.py`
  - `encoding_pipeline.py`

#### Connectors
- **Pattern**: `<stage>_connector_<type>.py`
- **Examples**:
  - `readers_connector_config.py`
  - `readers_connector_upstream.py`
  - `detect_type_connector_config.py`

#### Schemas
- **Pattern**: `<stage>_schema_<type>.py`
- **Examples**:
  - `readers_schema_types.py`
  - `readers_schema_output.py`
  - `detect_type_schema_types.py`

#### Internal Helpers
- **Pattern**: `<stage>_helper_<topic>.py`
- **Examples**:
  - `readers_helper_logging.py`
  - `detect_type_helper_detection.py`

#### Tests
- **Pattern**: `test_<stage>_<module>.py`
- **Examples**:
  - `test_readers_core_pdf.py`
  - `test_detect_type_pipeline.py`
  - `test_encoding_config.py`

### Main Layer Files

#### Cross-Phase Helpers
- **Pattern**: `main_pre_helpers_<topic>.py`
- **Examples**:
  - `main_pre_helpers_lang.py`
  - `main_pre_helpers_logger.py`
  - `main_pre_helpers_image.py`
  - `main_pre_helpers_num.py`

#### Multi-Phase Pipelines
- **Pattern**: `<purpose>_pipeline.py`
- **Examples**:
  - `preprocessing_chain.py`
  - `detect_and_read.py`
  - `smoke_test_pipeline.py`

#### Global Schemas
- **Pattern**: `<entity>_schema.py`
- **Examples**:
  - `document_meta_schema.py`
  - `stage_contract_schema.py`
  - `pipeline_config_schema.py`

#### Global Tests
- **Pattern**: `test_<topic>.py`
- **Examples**:
  - `test_main_pre_helpers_lang.py`
  - `test_pipeline_integration.py`

## Function Naming Rules

### Phase Functions
- **Pattern**: `<verb>_<stage>_<functionality>`
- **Examples**:
  - `process_readers_segment`
  - `compute_readers_table_bbox`
  - `record_readers_table_candidate`

### Main Functions
- **Pattern**: `<verb>_main_pre_<topic>`
- **Examples**:
  - `compute_main_pre_helpers_lang`
  - `process_main_pre_helpers_image`

### Pipeline Functions
- **Single Phase**: `run_<stage>_pipeline`
  - `run_readers_pipeline`
  - `run_detect_type_pipeline`
- **Multi Phase**: `run_<purpose>_pipeline`
  - `run_preprocessing_chain`
  - `run_detect_and_read`

## Directory Naming Rules

### Phase Directories
- **Pattern**: `phase_XX_<stage>`
- **Examples**:
  - `phase_00_detect_type`
  - `phase_01_encoding`
  - `phase_02_readers`

### Main Directories
- **Pattern**: `main_pre_<purpose>`
- **Examples**:
  - `main_pre_helpers`
  - `main_pre_schemas`
  - `main_pre_pipeline`
  - `main_pre_config`
  - `main_pre_standards`

## Configuration Files

### Phase Configuration
- **Pattern**: `<stage>_config_<type>.py`
- **Examples**:
  - `readers_config_profiles.py`
  - `detect_type_config_loader.py`

### Global Configuration
- **Pattern**: `<topic>_config.yaml`
- **Examples**:
  - `pipeline_config.yaml`
  - `validation_rules.yaml`
  - `logging_config.yaml`

## Validation Rules

### Valid Examples
- `phase_00_detect_type` ✓
- `readers_core_pdf.py` ✓
- `test_readers_core_pdf.py` ✓
- `main_pre_helpers_lang.py` ✓

### Invalid Examples
- `phase_2_readers` ✗ (missing leading zero)
- `Phase_02_Readers` ✗ (wrong case)
- `OCR_Reader.py` ✗ (wrong case and pattern)
- `reader.py` ✗ (missing stage prefix)

## Common Patterns

### Stage Names
- Use lowercase with underscores
- Be descriptive and concise
- Examples: `detect_type`, `encoding`, `readers`, `segmentation`

### Functionality Names
- Use lowercase with underscores
- Be specific about what the function does
- Examples: `pdf`, `ocr`, `classifier`, `normalizer`

### Topic Names
- Use lowercase with underscores
- Be descriptive of the utility purpose
- Examples: `lang`, `logger`, `image`, `num`, `geom`

## Migration Notes

- Files using old patterns should be renamed to match new standards
- Update all import statements when renaming files
- Maintain backward compatibility during transition period
- Use phase generator script for new phases to ensure compliance

## Cross-Phase Code Classification

### Decision Tree
1. **Is this code used by more than one phase?**
   - **No**: Place in phase-specific folder
   - **Yes**: Continue to step 2

2. **Determine code category:**
   - **Utility Functions**: `main_pre_helpers/` - Pure utility functions (math, text, file operations)
   - **Orchestration**: `main_pre_pipeline/` - Multi-phase coordination and workflow management
   - **Data Structures**: `main_pre_schemas/` - Shared schemas, contracts, and type definitions
   - **Configuration**: `main_pre_config/` - Global configuration and rules
   - **Output Management**: `main_pre_output/` - Cross-phase output management and routing
   - **Testing**: `main_pre_tests/` - Cross-phase integration and system tests
   - **Samples**: `main_pre_samples/` - Sample data and test files

## Standards Compliance

### Phase Generator
The phase generator script automatically creates phases that comply with these naming standards.

### Validation
- Use the validation script to check naming compliance
- All new files must follow the established patterns
- Import statements must be updated when files are renamed

### Enforcement
- Code reviews should verify naming compliance
- CI/CD pipelines can include naming validation checks
- Documentation should reference these standards
