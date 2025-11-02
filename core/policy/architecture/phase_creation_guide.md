# Phase Creation Guide

This guide provides step-by-step instructions for creating a new phase in the preprocessing pipeline.

## Prerequisites

- Python 3.8+ installed
- Git repository access
- Understanding of phase structure requirements

## Quick Start

### 1. Create Phase Directory Structure

```bash
# Create main phase directory
mkdir -p phase_XX_<stage_name>

# Create required subdirectories
mkdir -p phase_XX_<stage_name>/{
    config,
    pipeline_workflow,
    connecters,
    core_functions,
    schemas,
    outputs,
    internal_helpers,
    tests,
    common_files/{docs,git,configs,policies,others}
}
```

### 2. Initialize Python Packages

```bash
# Create __init__.py files
touch phase_XX_<stage_name>/__init__.py
touch phase_XX_<stage_name>/{config,pipeline_workflow,connecters,core_functions,schemas,outputs,internal_helpers,tests}/__init__.py
```

### 3. Copy Essential Files

Copy the following files from an existing phase:
- `common_files/docs/README.md` (customize for your phase)
- `common_files/docs/CHANGELOG.md` (start with initial version)
- `common_files/git/Makefile` (customize build commands)
- `common_files/git/.gitmessage` (customize commit template)
- `common_files/configs/ENV.sample` (customize environment variables)
- `common_files/configs/LOGGING_BASE.yaml` (customize logging)
- `common_files/configs/SETTINGS_BASE.yaml` (customize settings)

### 4. Implement Core Components

#### 4.1 Create Schema Files
Create `schemas/<stage_name>_schema_types.py`:
```python
"""Type definitions for <stage_name> phase."""

from typing import TypedDict, List, Dict, Any

class <StageName>Input(TypedDict):
    """Input contract for <stage_name> phase."""
    items: List[Dict[str, Any]]

class <StageName>Output(TypedDict):
    """Output contract for <stage_name> phase."""
    result: Dict[str, Any]
    stats: Dict[str, Any]
```

#### 4.2 Create Core Functions
Create `core_functions/<stage_name>_core_process.py`:
```python
"""Core processing logic for <stage_name> phase."""

def process_<stage_name>_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process items through <stage_name> phase."""
    # Implementation here
    pass
```

#### 4.3 Create Pipeline Workflow
Create `pipeline_workflow/<stage_name>_pipeline.py`:
```python
"""Pipeline orchestration for <stage_name> phase."""

def run_<stage_name>_pipeline(
    generic_items: List[Dict[str, Any]],
    io_config: Dict[str, Any],
    options_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Main entry point for <stage_name> pipeline."""
    # Implementation here
    pass
```

### 5. Set Up Testing

Create `tests/test_<stage_name>_core.py`:
```python
"""Tests for <stage_name> core functions."""

import pytest
from ..core_functions.<stage_name>_core_process import process_<stage_name>_items

def test_process_<stage_name>_items():
    """Test basic processing functionality."""
    # Test implementation here
    pass
```

### 6. Validation

#### 6.1 Run Tests
```bash
python -m pytest tests/ -v
```

#### 6.2 Check Imports
```bash
python -c "from phase_XX_<stage_name>.pipeline_workflow.<stage_name>_pipeline import run_<stage_name>_pipeline; print('Import successful')"
```

## Common Pitfalls

1. **Missing __init__.py files**: Ensure all directories have proper Python package initialization
2. **Import path issues**: Use relative imports within the phase
3. **Configuration validation**: Always validate configuration on startup
4. **Error handling**: Implement comprehensive error handling
5. **Testing coverage**: Ensure adequate test coverage

## Next Steps

After phase initialization:
1. Implement core functionality
2. Add comprehensive tests
3. Update documentation
4. Integrate with main pipeline
5. Deploy and monitor

## Support

For questions or issues:
- Check existing phase examples
- Review this guide
- Contact development team
- Create issue in repository
