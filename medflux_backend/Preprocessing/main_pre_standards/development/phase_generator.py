#!/usr/bin/env python3
"""
Phase Generator Script

This script creates a new phase with the minimal required structure.
Replaces the manual INIT_PHASE.md process with automated generation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
import argparse
import yaml
from datetime import datetime


def create_directory_structure(phase_path: Path) -> None:
    """Create the required directory structure for a new phase."""
    
    directories = [
        "config",
        "pipeline_workflow", 
        "connecters",
        "core_functions",
        "schemas",
        "outputs",
        "internal_helpers",
        "tests",
        "common_files/docs",
        "common_files/git",
        "common_files/configs",
        "common_files/policies",
        "common_files/others"
    ]
    
    for directory in directories:
        dir_path = phase_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def create_init_files(phase_path: Path, phase_name: str) -> None:
    """Create __init__.py files for Python packages."""
    
    init_dirs = [
        "",
        "config",
        "pipeline_workflow",
        "connecters", 
        "core_functions",
        "schemas",
        "outputs",
        "internal_helpers",
        "tests"
    ]
    
    for init_dir in init_dirs:
        init_path = phase_path / init_dir / "__init__.py"
        init_path.write_text(f'"""Package initialization for {phase_name}."""\n')
        print(f"Created: {init_path}")


def create_schema_files(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create schema files for the phase."""
    
    # Create types schema
    types_content = f'''"""Type definitions for {stage_name} phase."""

from typing import TypedDict, List, Dict, Any, Optional

class {stage_name.title()}Input(TypedDict):
    """Input contract for {stage_name} phase."""
    items: List[Dict[str, Any]]

class {stage_name.title()}Output(TypedDict):
    """Output contract for {stage_name} phase."""
    result: Dict[str, Any]
    stats: Dict[str, Any]

class {stage_name.title()}Config(TypedDict):
    """Configuration contract for {stage_name} phase."""
    options: Dict[str, Any]
    io: Dict[str, Any]
    features: Dict[str, Any]
'''
    
    schema_path = phase_path / "schemas" / f"{stage_name}_schema_types.py"
    schema_path.write_text(types_content)
    print(f"Created: {schema_path}")


def create_core_function(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create core function file."""
    
    core_content = f'''"""Core processing logic for {stage_name} phase."""

from typing import List, Dict, Any
from ..schemas.{stage_name}_schema_types import {stage_name.title()}Input, {stage_name.title()}Output


def process_{stage_name}_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process items through {stage_name} phase.
    
    Args:
        items: List of input items to process
        
    Returns:
        Dictionary containing processed results and statistics
    """
    # TODO: Implement core processing logic
    result = {{"processed_items": len(items), "status": "success"}}
    stats = {{"items_processed": len(items), "processing_time": 0.0}}
    
    return {{
        "unified_document": result,
        "stage_stats": stats
    }}
'''
    
    core_path = phase_path / "core_functions" / f"{stage_name}_core_process.py"
    core_path.write_text(core_content)
    print(f"Created: {core_path}")


def create_pipeline_workflow(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create pipeline workflow file."""
    
    pipeline_content = f'''"""Pipeline orchestration for {stage_name} phase."""

from typing import List, Dict, Any
from ..core_functions.{stage_name}_core_process import process_{stage_name}_items


def run_{stage_name}_pipeline(
    generic_items: List[Dict[str, Any]],
    io_config: Dict[str, Any],
    options_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Main entry point for {stage_name} pipeline.
    
    Args:
        generic_items: Input items to process
        io_config: I/O configuration
        options_config: Processing options
        
    Returns:
        Dictionary containing pipeline results
    """
    # TODO: Implement pipeline orchestration
    return process_{stage_name}_items(generic_items)
'''
    
    pipeline_path = phase_path / "pipeline_workflow" / f"{stage_name}_pipeline.py"
    pipeline_path.write_text(pipeline_content)
    print(f"Created: {pipeline_path}")


def create_test_file(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create test file."""
    
    test_content = f'''"""Tests for {stage_name} core functions."""

import pytest
from ..core_functions.{stage_name}_core_process import process_{stage_name}_items


def test_process_{stage_name}_items():
    """Test basic processing functionality."""
    # Test data
    test_items = [
        {{"id": "test_1", "data": "sample_data"}},
        {{"id": "test_2", "data": "another_sample"}}
    ]
    
    # Run processing
    result = process_{stage_name}_items(test_items)
    
    # Assertions
    assert "unified_document" in result
    assert "stage_stats" in result
    assert result["stage_stats"]["items_processed"] == 2
    assert result["unified_document"]["status"] == "success"
'''
    
    test_path = phase_path / "tests" / f"test_{stage_name}_core.py"
    test_path.write_text(test_content)
    print(f"Created: {test_path}")


def create_common_files(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create essential common files."""
    
    # README.md
    readme_content = f'''# {stage_name.title()} Stage ({phase_name})

## Purpose
TODO: Describe the purpose of this stage.

## Workflow
- Orchestrator: pipeline_workflow/{stage_name}_pipeline.py
- Connectors: connecters/*
- Core processors: core_functions/*
- Schemas: schemas/*
- Helpers: internal_helpers/*
- Outputs: outputs/*

## Outputs
- cfg['io']['out_doc_path'] (unified_document)
- cfg['io']['out_stats_path'] (stage_stats)

## How to Run
```bash
make run INPUTS="samples/sample_file.txt"
```
Override `INPUTS` with one or more paths (space separated) that should be processed.

## Validation
Run stage checks before committing changes.

```bash
make validate
```

## Change Log
Entries are appended automatically by the documentation updater after each change. Replace the TODO text in each entry with real context when you review the update.

### change-{datetime.now().strftime("%Y%m%dT%H%M%S")}-initial
- What changed: Initial phase setup for {stage_name} stage.
- Why it was needed: New phase created for {stage_name} processing.
- Result: Phase structure created with basic functionality.
'''
    
    readme_path = phase_path / "common_files" / "docs" / "README.md"
    readme_path.write_text(readme_content)
    print(f"Created: {readme_path}")
    
    # CHANGELOG.md
    changelog_content = f'''# Changelog

All notable changes to the {stage_name} stage will be documented in this file.

## [1.0.0] - {datetime.now().strftime("%Y-%m-%d")}

### Added
- Initial phase setup
- Basic processing structure
- Test framework
- Documentation templates
'''
    
    changelog_path = phase_path / "common_files" / "docs" / "CHANGELOG.md"
    changelog_path.write_text(changelog_content)
    print(f"Created: {changelog_path}")
    
    # Makefile
    makefile_content = f'''# {stage_name.title()} Stage Makefile

.PHONY: run validate clean test

# Default target
all: validate

# Run the stage
run:
\tpython -m {phase_name}.pipeline_workflow.{stage_name}_pipeline

# Validate the stage
validate:
\tpython -m pytest {phase_name}/tests/ -v
\tpython -c "from {phase_name}.pipeline_workflow.{stage_name}_pipeline import run_{stage_name}_pipeline; print('Import successful')"

# Run tests
test:
\tpython -m pytest {phase_name}/tests/ -v

# Clean up
clean:
\tfind . -type f -name "*.pyc" -delete
\tfind . -type d -name "__pycache__" -delete
'''
    
    makefile_path = phase_path / "common_files" / "git" / "Makefile"
    makefile_path.write_text(makefile_content)
    print(f"Created: {makefile_path}")
    
    # .gitmessage
    gitmessage_content = f'''# {stage_name.title()} Stage Commit Message

# Type: feat|fix|docs|style|refactor|test|chore
# Scope: {stage_name}|config|tests|docs
# Subject: Brief description of changes

# Body: Detailed description of changes
# 
# Footer: Breaking changes, issues fixed, etc.

# Example:
# feat({stage_name}): add new processing feature
# 
# Add new feature to process additional file types
# 
# Closes #123
'''
    
    gitmessage_path = phase_path / "common_files" / "git" / ".gitmessage"
    gitmessage_path.write_text(gitmessage_content)
    print(f"Created: {gitmessage_path}")


def create_config_files(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create configuration files."""
    
    # ENV.sample
    env_content = f'''# {stage_name.title()} Stage Environment Variables

# Processing options
{stage_name.upper()}_MODE=default
{stage_name.upper()}_LANG=deu+eng
{stage_name.upper()}_DPI=300

# I/O configuration
{stage_name.upper()}_OUT_ROOT=outputs/{phase_name}
{stage_name.upper()}_CACHE_DIR=/tmp/{stage_name}_cache
{stage_name.upper()}_MAX_WORKERS=4

# Feature flags
{stage_name.upper()}_ENABLE_OCR=true
{stage_name.upper()}_ENABLE_TABLES=true
{stage_name.upper()}_ENABLE_LANG_DETECT=true

# Thresholds
{stage_name.upper()}_CONFIDENCE_MIN=0.7
{stage_name.upper()}_OCR_LOW_CONF=75.0
{stage_name.upper()}_SUSPICIOUS_TEXT_CHARS_MIN=40
'''
    
    env_path = phase_path / "common_files" / "configs" / "ENV.sample"
    env_path.write_text(env_content)
    print(f"Created: {env_path}")
    
    # LOGGING_BASE.yaml
    logging_content = f'''# {stage_name.title()} Stage Logging Configuration

logging:
  version: 1
  disable_existing_loggers: false
  
  formatters:
    standard:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    detailed:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
  
  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: standard
      stream: ext://sys.stdout
    
    file:
      class: logging.FileHandler
      level: DEBUG
      formatter: detailed
      filename: logs/{stage_name}.log
      mode: a
  
  loggers:
    {phase_name}:
      level: DEBUG
      handlers: [console, file]
      propagate: false
  
  root:
    level: INFO
    handlers: [console]
'''
    
    logging_path = phase_path / "common_files" / "configs" / "LOGGING_BASE.yaml"
    logging_path.write_text(logging_content)
    print(f"Created: {logging_path}")
    
    # SETTINGS_BASE.yaml
    settings_content = f'''# {stage_name.title()} Stage Settings

stage:
  name: "{stage_name}"
  version: "1.0.0"
  description: "Processing stage for {stage_name}"
  
  inputs:
    - name: "generic_items"
      type: "array"
      description: "Generic input collection"
  
  outputs:
    - name: "unified_document"
      type: "json"
      description: "Unified document payload"
    - name: "stage_stats"
      type: "json"
      description: "Aggregated stage metrics"

options:
  mode: "default"
  lang: "deu+eng"
  dpi: 300
  psm: 6
  tables_mode: "detect"
  blocks_threshold: 3

io:
  out_root: "outputs/{phase_name}"
  cache_dir: "/tmp/{stage_name}_cache"
  max_workers: 4

features:
  enable_ocr: true
  enable_tables: true
  enable_lang_detect: true

thresholds:
  confidence_min: 0.7
  ocr_low_conf: 75.0
  suspicious_text_chars_min: 40
'''
    
    settings_path = phase_path / "common_files" / "configs" / "SETTINGS_BASE.yaml"
    settings_path.write_text(settings_content)
    print(f"Created: {settings_path}")


def main():
    """Main function to generate a new phase."""
    
    parser = argparse.ArgumentParser(description="Generate a new phase")
    parser.add_argument("phase_number", type=int, help="Phase number (e.g., 03)")
    parser.add_argument("stage_name", help="Stage name (e.g., segment)")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    
    args = parser.parse_args()
    
    # Create phase name
    phase_name = f"phase_{args.phase_number:02d}_{args.stage_name}"
    stage_name = args.stage_name
    
    # Create phase path
    phase_path = Path(args.output_dir) / phase_name
    
    print(f"Generating phase: {phase_name}")
    print(f"Output directory: {phase_path}")
    
    # Create directory structure
    create_directory_structure(phase_path)
    
    # Create Python package files
    create_init_files(phase_path, phase_name)
    
    # Create core files
    create_schema_files(phase_path, phase_name, stage_name)
    create_core_function(phase_path, phase_name, stage_name)
    create_pipeline_workflow(phase_path, phase_name, stage_name)
    create_test_file(phase_path, phase_name, stage_name)
    
    # Create common files
    create_common_files(phase_path, phase_name, stage_name)
    create_config_files(phase_path, phase_name, stage_name)
    
    print(f"\nPhase {phase_name} generated successfully!")
    print(f"Next steps:")
    print(f"1. cd {phase_path}")
    print(f"2. python -m pytest tests/ -v")
    print(f"3. Customize the implementation in core_functions/")
    print(f"4. Update documentation in common_files/docs/")


if __name__ == "__main__":
    main()
