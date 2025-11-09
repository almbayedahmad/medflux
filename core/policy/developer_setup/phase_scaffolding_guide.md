# Phase Scaffolding Guide

Focused instructions for creating and scaffolding a new phase consistently.
For environment setup and end-to-end development checklist, see:
- core/policy/developer_setup/environment_setup.md
- core/policy/developer_setup/development_checklist.md

## Phase Initialization Checklist

### 1) Pre-Initialization
- [ ] Verify phase requirements and dependencies
- [ ] Check naming conventions (stage and files)
- [ ] Validate phase order and references to other phases

### 2) Directory Structure Creation
- [ ] Create phase root directory
- [ ] Create required subdirectories (domain, domain/ops, cli, connectors, io, schemas, tests, common_files)
- [ ] Add `__init__.py` where needed
- [ ] Verify final structure matches standards (see v2 layout in backend/Preprocessing/README.md)

### 3) Template File Copying
- [ ] Copy common stage templates
- [ ] Copy phase-specific templates
- [ ] Replace placeholders
- [ ] Verify file permissions and integrity

### 4) Configuration Setup
- [ ] Create baseline config files (YAML)
- [ ] Set sensible defaults
- [ ] Validate syntax and loading
- [ ] Document configuration options

### 5) Code Generation
- [ ] Generate domain modules (domain/process.py and domain/ops/* as needed)
- [ ] Generate v2 API (`api.py`) and CLI (`cli/*_cli_v2.py`)
- [ ] Define schemas and types
- [ ] Seed tests (unit/integration)
- [ ] Seed documentation (README, CHANGELOG)

## File Generation Rules

### Core Functions
- Generate from templates; include imports, type hints, docstrings, error handling

### Pipeline Workflow
- Provide orchestration entry, logging, error handling, and basic monitoring hooks

### Schemas
- Define types/contracts; include validation rules, examples, and versioning markers

### Tests
- Generate unit and integration tests; include fixtures and sample data when applicable

### Documentation
- Generate README, API notes, usage examples, troubleshooting, and changelog stub

## Template Processing

### Placeholder Replacement
- `{{PHASE_NAME}}`, `{{PHASE_ID}}`, `{{PHASE_VERSION}}`, `{{CREATED_AT}}`, `{{AUTHOR}}`
- `{{INPUTS}}`, `{{OUTPUTS}}`, `{{STANDARD_OUTPUT_PATH}}`, `{{SAMPLE_OUTPUT_PATH}}`, `{{SCHEMA_VERSION}}`

### Template Validation
- Confirm all placeholders replaced
- Validate template syntax
- Verify file permissions and integrity
