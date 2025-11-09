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
        "cli",
        "connectors",
        "domain",
        "domain/ops",
        "io",
        "schemas",
        "common_files/docs",
        "common_files/git",
        "common_files/configs",
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
        "cli",
        "connectors",
        "domain",
        "domain/ops",
        "io",
        "schemas",
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
    """Create domain processing file (v2 layout)."""

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

    core_path = phase_path / "domain" / "process.py"
    core_path.write_text(core_content)
    print(f"Created: {core_path}")


def create_pipeline_workflow(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create v2 API and CLI files (no legacy pipeline_workflow)."""

    api_content = f'''# PURPOSE:
#   Phase public API and PhaseRunner implementation.
# OUTCOME:
#   Standardized lifecycle while preserving a simple public entrypoint.

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from core.preprocessing.phase_api import PhaseRunner, PhaseSpec
from core.preprocessing.config.registry import merge_overrides

from .domain.process import process_{stage_name}_items


class {stage_name.title()}Runner(PhaseRunner[Dict[str, Any], Dict[str, Any]]):
    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return merge_overrides({{}}, overrides)

    def _process(self, upstream: Sequence[Dict[str, Any]], *, config: Dict[str, Any]) -> Dict[str, Any]:
        return process_{stage_name}_items(list(upstream))


def run_{stage_name}(generic_items: Sequence[Dict[str, Any]] | None = None, *, config_overrides: Dict[str, Any] | None = None, run_id: str | None = None) -> Dict[str, Any]:
    runner = {stage_name.title()}Runner(PhaseSpec(phase_id="phase_xx_{stage_name}", name="{stage_name}"))
    result = runner.run(generic_items, config_overrides=config_overrides, run_id=run_id)
    payload = result.get("payload", {{}})
    final: Dict[str, Any] = {{"config": result["config"], **payload}}
    if "run_id" in result:
        final["run_id"] = result["run_id"]
    return final
'''

    api_path = phase_path / "api.py"
    api_path.write_text(api_content)
    print(f"Created: {api_path}")

    cli_content = f'''# PURPOSE:
#   Unified CLI entrypoint using the shared CLI toolkit.
# OUTCOME:
#   Consistent flags across phases.

from __future__ import annotations

from core.preprocessing.cli.common import run_phase_cli
from core.preprocessing.phase_api import PhaseSpec
from ..api import {stage_name.title()}Runner


def main(argv: list[str] | None = None) -> int:
    return run_phase_cli(
        {stage_name.title()}Runner,
        spec_kwargs={{"phase_id": "phase_xx_{stage_name}", "name": "{stage_name}"}},
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
'''
    cli_path = phase_path / "cli" / f"{stage_name}_cli_v2.py"
    cli_path.write_text(cli_content)
    print(f"Created: {cli_path}")


def create_test_file(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create root-level unit test only (no phase-local tests)."""

    test_content = f'''"""Tests for {stage_name} domain functions."""

import pytest
from ..domain.process import process_{stage_name}_items


def test_process_{stage_name}_items() -> None:
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

    # phase-local tests are not created; tests live under root `tests/`

    # Also create a root-level unit test under tests/unit/phases
    try:
        pkg = str(phase_path.resolve().relative_to(Path.cwd().resolve())).replace("\\", ".").replace("/", ".")
    except Exception:
        pkg = phase_name

    test_content_root = f'''# PURPOSE:
#   Unit tests for {stage_name} domain functions.
# OUTCOME:
#   Verifies minimal processing functionality for generated scaffolds.\n
import pytest
from {pkg}.domain.process import process_{stage_name}_items


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

    tests_root = phase_path.parent / "tests" / "unit" / "phases" / phase_name
    tests_root.mkdir(parents=True, exist_ok=True)
    test_path_root = tests_root / f"test_{stage_name}_core.py"
    test_path_root.write_text(test_content_root)
    print(f"Created: {test_path_root}")


def create_common_files(phase_path: Path, phase_name: str, stage_name: str) -> None:
    """Create essential common files."""

    # README.md
    readme_content = f'''# {stage_name.title()} Stage ({phase_name})

## Purpose
TODO: Describe the purpose of this stage.

## Workflow
- API: `api.py` (PhaseRunner-based)
- CLI: `cli/{stage_name}_cli_v2.py`
- Connectors: `connectors/*`
- Domain: `domain/*`
- IO: `io/*`
- Schemas: `schemas/*`

## Outputs
- `cfg['io']['out_doc_path']` (unified_document)
- `cfg['io']['out_stats_path']` (stage_stats)

## How to Run

Preferred (umbrella CLI):
```bash
medflux phase-{stage_name} --inputs samples/sample_file.txt --output-root ./.artifacts/{stage_name}
```

Phase-local v2 CLI:
```bash
python -m backend.Preprocessing.{phase_name}.cli.{stage_name}_cli_v2 samples/sample_file.txt
```

Pass one or more input items/paths as arguments.

## Env & Logging
- Use the root `.env.example` for environment variables (copy to `.env` if needed).
- Logging is policy-driven under `core/policy/observability/logging/` and applied via `core.logging.configure_logging()`.
  - CLI flags `--log-level`, `--log-json`, `--log-stderr` are available (umbrella + v2 CLIs).

## Validation
Run repo tests before committing changes.

```bash
pytest -q tests
```
'''

    readme_path = phase_path / "common_files" / "docs" / "README.md"
    readme_path.write_text(readme_content)
    print(f"Created: {readme_path}")

    # Per-phase CHANGELOG.md is retired; entries are kept in the root CHANGELOG.

    # Makefile
    makefile_content = f'''# {stage_name.title()} Stage Makefile (v2)

.PHONY: run validate test clean

# Run the stage (v2 CLI; pass INPUTS="file1 file2" OUTPUT_ROOT=./.artifacts/{stage_name} RUN_ID=123)
run:
	python -m backend.Preprocessing.{phase_name}.cli.{stage_name}_cli_v2 \
		$$(if [ -n "$${INPUTS}" ]; then echo $${INPUTS}; fi) \
		$$(if [ -n "$${OUTPUT_ROOT}" ]; then echo --output-root $${OUTPUT_ROOT}; fi) \
		$$(if [ -n "$${RUN_ID}" ]; then echo --run-id $${RUN_ID}; fi)

# Validate using root tests
validate: test

test:
	pytest -q tests

clean:
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name "__pycache__" -delete || true
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
    print("Next steps:")
    print("1. From repo root, run: pytest -q tests")
    print(f"2. Try umbrella CLI: medflux phase-{stage_name} --inputs <files> --output-root ./.artifacts/{stage_name}")
    print("3. Customize the implementation in domain/ and domain/ops/")
    print("4. Update documentation in common_files/docs/")


if __name__ == "__main__":
    main()
