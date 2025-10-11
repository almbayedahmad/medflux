#!/usr/bin/env python3
"""Validate a stage against the v6 consolidated standards."""
from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    def ok(self) -> bool:
        return not self.errors


def load_v6_standards() -> dict:
    """Load the consolidated v6 standards file."""
    standards_path = Path(__file__).parent.parent / "standards" / "tree_structure_with_layers_and_rules_v6.yaml"
    if not standards_path.exists():
        raise SystemExit(f"Standards file not found: {standards_path}")

    data = yaml.safe_load(standards_path.read_text(encoding="utf-8"))
    return data or {}


def infer_stage_slug(stage_root: Path) -> str:
    """Extract stage slug from directory name."""
    match = re.match(r"^phase_\d{2}_(?P<slug>[a-z0-9_]+)$", stage_root.name)
    if match:
        return match.group("slug")
    return stage_root.name.lower()


def validate_tree(stage_root: Path, standards: dict, result: ValidationResult) -> None:
    """Validate directory structure against v6 standards."""
    tree_structure = standards.get("tree_structure", {})
    phase_structure = tree_structure.get("phase_directory_structure", {})

    # Get required folders from v6 standards
    required_folders = [
        "config",
        "core_functions",
        "connecters",
        "schemas",
        "outputs",
        "internal_helpers",
        "pipeline_workflow",
        "tests",
        "common_files"
    ]

    for folder in required_folders:
        if not (stage_root / folder).exists():
            result.errors.append(f"missing required folder: {folder}")


def validate_naming(stage_root: Path, standards: dict, stage_slug: str, result: ValidationResult) -> None:
    """Validate file naming against v6 standards."""
    naming_conventions = standards.get("tree_structure", {}).get("unified_naming_conventions", {})
    file_naming_rules = naming_conventions.get("file_naming_rules", {})

    # Get naming patterns from v6 standards
    phase_layer = file_naming_rules.get("phase_layer", {})

    # Validate core functions naming
    core_pattern = phase_layer.get("core_functions", {}).get("pattern", "<stage>_core_<functionality>.py")
    validate_files_in_folder(stage_root / "core_functions", core_pattern, stage_slug, result)

    # Validate pipeline naming
    pipeline_pattern = phase_layer.get("pipeline_workflow", {}).get("pattern", "<stage>_pipeline.py")
    validate_files_in_folder(stage_root / "pipeline_workflow", pipeline_pattern, stage_slug, result)

    # Validate connector naming
    connector_pattern = phase_layer.get("connecters", {}).get("pattern", "<stage>_connector_<type>.py")
    validate_files_in_folder(stage_root / "connecters", connector_pattern, stage_slug, result)

    # Validate schema naming
    schema_pattern = phase_layer.get("schemas", {}).get("pattern", "<stage>_schema_<type>.py")
    validate_files_in_folder(stage_root / "schemas", schema_pattern, stage_slug, result)

    # Validate helper naming
    helper_pattern = phase_layer.get("internal_helpers", {}).get("pattern", "<stage>_helper_<topic>.py")
    validate_files_in_folder(stage_root / "internal_helpers", helper_pattern, stage_slug, result)


def validate_files_in_folder(folder_path: Path, pattern: str, stage_slug: str, result: ValidationResult) -> None:
    """Validate files in a specific folder against naming pattern."""
    if not folder_path.exists():
        return

    # Convert pattern to regex
    regex_pattern = pattern.replace("<stage>", stage_slug).replace("<functionality>", r"[a-z0-9_]+").replace("<type>", r"[a-z0-9_]+").replace("<topic>", r"[a-z0-9_]+")
    regex_pattern = regex_pattern.replace(".py", r"\.py$")

    for file_path in folder_path.glob("*.py"):
        if not re.match(regex_pattern, file_path.name):
            result.warnings.append(f"file naming may not follow pattern: {file_path.name} (expected pattern: {pattern})")


def validate_functions(stage_root: Path, standards: dict, stage_slug: str, result: ValidationResult) -> None:
    """Validate function naming against v6 standards."""
    naming_conventions = standards.get("tree_structure", {}).get("unified_naming_conventions", {})
    function_rules = naming_conventions.get("function_naming_rules", {})

    # Get function patterns from v6 standards
    phase_functions = function_rules.get("phase_functions", {})
    function_pattern = phase_functions.get("pattern", "<verb>_<stage>_<functionality>")

    # Check for forbidden terms
    forbidden_terms = ["loader", "load"]

    for py_file in stage_root.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name

                    # Check for forbidden terms
                    for term in forbidden_terms:
                        if term in func_name.lower():
                            result.errors.append(f"function '{func_name}' in {py_file} contains forbidden term '{term}'")

                    # Check naming pattern (basic check)
                    if not re.match(r"^[a-z_]+_[a-z0-9_]+_[a-z0-9_]+$", func_name):
                        if not func_name.startswith("_"):  # Allow private functions
                            result.warnings.append(f"function '{func_name}' in {py_file} may not follow naming pattern")

        except (SyntaxError, UnicodeDecodeError):
            result.warnings.append(f"could not parse {py_file} for function validation")


def validate_language(stage_root: Path, standards: dict, result: ValidationResult) -> None:
    """Validate language policy compliance."""
    # Check for English-only content
    for file_path in stage_root.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            # Basic check for non-ASCII characters that might indicate non-English content
            if any(ord(char) > 127 for char in content if char.isalpha()):
                result.warnings.append(f"file {file_path} may contain non-English content")
        except UnicodeDecodeError:
            result.warnings.append(f"could not read {file_path} for language validation")


def main() -> None:
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate a stage against v6 consolidated standards")
    parser.add_argument("--stage-root", required=True, type=Path, help="Path to stage root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show warnings")

    args = parser.parse_args()

    if not args.stage_root.exists():
        print(f"ERROR: Stage root directory does not exist: {args.stage_root}")
        sys.exit(1)

    try:
        standards = load_v6_standards()
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    result = ValidationResult(errors=[], warnings=[])
    stage_slug = infer_stage_slug(args.stage_root)

    print(f"Validating stage: {args.stage_root.name} (slug: {stage_slug})")

    # Run validations
    validate_tree(args.stage_root, standards, result)
    validate_naming(args.stage_root, standards, stage_slug, result)
    validate_functions(args.stage_root, standards, stage_slug, result)
    validate_language(args.stage_root, standards, result)

    # Report results
    if result.errors:
        print("ERRORS:")
        for error in result.errors:
            print(f"  - {error}")

    if args.verbose and result.warnings:
        print("WARNINGS:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.ok():
        print("✅ Validation passed")
        sys.exit(0)
    else:
        print("❌ Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
