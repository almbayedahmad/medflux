# Agent Standards - Consolidated Structure

This directory contains the consolidated agent standards, automation tools, and development utilities for the medflux preprocessing pipeline.

## Directory Structure

```
agent/
├── standards/                    # Consolidated standards and guidelines
│   ├── tree_structure_with_layers_and_rules_v6.yaml    # Main comprehensive standards
│   ├── agent_workflow.md                                # Consolidated workflow instructions
│   ├── environment_setup.md                             # Environment requirements
│   ├── git_configuration.md                             # Git setup and configuration
│   └── smoke_testing.md                                  # Smoke testing checklist
├── automation/                   # Automation scripts and pipelines
│   ├── change_pipeline.yaml                             # Change automation pipeline
│   ├── auto_documentation_update.py                     # Documentation automation
│   └── v6_validator.py                                  # Validation using v6 standards
└── tools/                       # Development tools and utilities
    └── stage_builder_op/                                 # Phase creation tools
        ├── stage_builder_v2.py                          # Main phase builder script
        ├── manifests/                                   # Builder manifests
        └── templates/                                   # Phase templates
```

## Key Features

### ✅ **Consolidated Standards**
- **Single Source of Truth**: All standards in `tree_structure_with_layers_and_rules_v6.yaml`
- **Comprehensive Coverage**: Architecture, naming conventions, validation rules
- **No Duplication**: Eliminated scattered individual rule files

### ✅ **Streamlined Workflow**
- **Clear Process**: Step-by-step workflow in `agent_workflow.md`
- **Updated Automation**: All scripts reference actual existing files
- **Consistent Validation**: v6 validator uses consolidated standards

### ✅ **Organized Tools**
- **Phase Creation**: Automated phase builder with templates
- **Documentation**: Auto-updating documentation system
- **Validation**: Standards-compliant validation system

## Usage

### Creating a New Phase
```bash
python tools/stage_builder_op/stage_builder_v2.py --phase 11 --name validation
```

### Validating a Phase
```bash
python automation/v6_validator.py --stage-root path/to/phase_XX_stage
```

### Running Change Pipeline
```bash
# Load change pipeline configuration
python automation/change_pipeline.yaml --event new --stage path/to/stage
```

## Migration Benefits

### **Before Consolidation**
- ❌ 3 separate directories (`agents_rules/`, `agents_instructions/`, `agents_tasks/`)
- ❌ 6+ individual instruction files with duplicate content
- ❌ References to non-existent individual rule files
- ❌ Outdated validator referencing missing files
- ❌ Scattered, confusing structure

### **After Consolidation**
- ✅ 3 organized directories (`standards/`, `automation/`, `tools/`)
- ✅ 1 comprehensive workflow file
- ✅ All references point to actual existing files
- ✅ Updated validator using consolidated standards
- ✅ Clear, logical organization

## Files Summary

### **KEPT (7 files)**
- `standards/tree_structure_with_layers_and_rules_v6.yaml` - Main standards
- `standards/environment_setup.md` - Environment requirements
- `standards/git_configuration.md` - Git setup
- `standards/smoke_testing.md` - Testing checklist
- `automation/change_pipeline.yaml` - Change automation
- `automation/auto_documentation_update.py` - Documentation automation
- `tools/stage_builder_op/` - Phase creation tools

### **DELETED (4+ files)**
- `agents_instructions/AGENTS.md` - Referenced non-existent files
- `agents_instructions/Agent_instructions_change.md` - Referenced non-existent files
- `agents_instructions/Agent_instructions_session_policy.md` - Referenced non-existent files
- `agents_tasks/validation_op/standards_validator.py` - Referenced non-existent files

### **CREATED (2 files)**
- `standards/agent_workflow.md` - Consolidated workflow instructions
- `automation/v6_validator.py` - New validator using v6 standards

## Standards Compliance

All tools and processes now use the consolidated v6 standards:
- **File Naming**: Follows `<stage>_<role>_<action>` patterns
- **Directory Structure**: Standardized phase structure
- **Function Naming**: Consistent verb-based patterns
- **Validation**: Comprehensive checks against actual standards

## Support

For questions about the agent standards:
- Check `standards/agent_workflow.md` for workflow guidance
- Review `standards/tree_structure_with_layers_and_rules_v6.yaml` for detailed standards
- Use `tools/stage_builder_op/` for phase creation
- Run `automation/v6_validator.py` for validation
