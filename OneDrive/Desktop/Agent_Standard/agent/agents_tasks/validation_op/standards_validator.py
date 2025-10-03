
#!/usr/bin/env python3
"""Validate a generated stage against the repository standards."""
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


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def infer_stage_slug(stage_root: Path) -> str:
    match = re.match(r"^phase_\d{2}_(?P<slug>[a-z0-9_]+)$", stage_root.name)
    if match:
        return match.group("slug")
    return stage_root.name.lower()


def validate_tree(stage_root: Path, tree_spec: dict, result: ValidationResult) -> None:
    required = tree_spec.get("required_subfolders", [])
    for folder in required:
        if not (stage_root / folder).exists():
            result.errors.append(f"missing required folder: {folder}")


def validate_naming(stage_root: Path, naming_spec: dict, stage_slug: str, result: ValidationResult) -> None:
    file_pattern = naming_spec.get("file_name_pattern")
    prefix_required = naming_spec.get("must_start_with_stage_prefix", False)
    prefix_placeholder = naming_spec.get("stage_prefix_placeholder", "<stage>_")
    forbidden_terms = naming_spec.get("forbidden_terms", [])
    rename_map = naming_spec.get("rename_map", {})

    stage_prefix = prefix_placeholder.replace("<stage>", stage_slug)

    if file_pattern:
        file_regex = re.compile(file_pattern)
    else:
        file_regex = None

    for py_file in stage_root.rglob("*.py"):
        relative_name = py_file.relative_to(stage_root)
        filename = py_file.name

        if filename == "__init__.py":
            continue

        if file_regex and not file_regex.match(filename):
            result.errors.append(f"{relative_name}: file name violates pattern {file_pattern}")

        if prefix_required and not filename.startswith(stage_prefix):
            parts = relative_name.parts
            if not parts or parts[0] != "tests":
                result.errors.append(f"{relative_name}: file name must start with '{stage_prefix}'")

        lowered = filename.lower()
        for term in forbidden_terms:
            if term in lowered:
                suggestion = rename_map.get(term, "")
                note = f"; suggested alternative: {suggestion}" if suggestion else ""
                result.errors.append(f"{relative_name}: forbidden term '{term}'{note}")

        _validate_function_names(py_file, naming_spec, relative_name, result)


def _validate_function_names(py_file: Path, naming_spec: dict, relative_name: Path, result: ValidationResult) -> None:
    pattern = naming_spec.get("function_name_pattern_strict")
    if not pattern:
        return

    func_regex = re.compile(pattern)
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except SyntaxError as exc:
        result.errors.append(f"{relative_name}: invalid Python syntax ({exc})")
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not func_regex.match(node.name):
                result.errors.append(
                    f"{relative_name}: function '{node.name}' violates pattern {pattern}"
                )


def validate_language(stage_root: Path, language_spec: dict, result: ValidationResult) -> None:
    if not language_spec:
        return

    extensions = language_spec.get("apply_to_extensions", [])
    forbidden = []
    if "arabic" in language_spec.get("forbid_scripts", []):
        forbidden.append(("arabic", re.compile(r"[؀-ۿ]")))

    if not forbidden:
        return

    for file in stage_root.rglob("*"):
        if not file.is_file():
            continue
        if extensions and file.suffix not in extensions:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in forbidden:
            if pattern.search(text):
                result.errors.append(f"{file.relative_to(stage_root)}: contains forbidden script ({label})")
                break


def validate_additional_regex(stage_root: Path, validation_spec: dict, result: ValidationResult) -> None:
    regex_section = validation_spec.get("regex", {})
    file_allowed = regex_section.get("file_allowed")
    forbidden_terms_regex = regex_section.get("forbidden_terms")

    allowed_re = re.compile(file_allowed) if file_allowed else None
    forbidden_re = re.compile(forbidden_terms_regex) if forbidden_terms_regex else None

    for py_file in stage_root.rglob("*.py"):
        relative_name = py_file.relative_to(stage_root)
        filename = py_file.name

        if allowed_re and not allowed_re.match(filename):
            result.errors.append(f"{relative_name}: does not match allowed file pattern {file_allowed}")

        if forbidden_re and forbidden_re.search(filename):
            result.errors.append(f"{relative_name}: matches forbidden term policy {forbidden_terms_regex}")


def validate_stage(standards_dir: Path, stage_root: Path) -> ValidationResult:
    result = ValidationResult(errors=[], warnings=[])

    if not standards_dir.exists():
        raise FileNotFoundError(f"standards directory not found: {standards_dir}")
    if not stage_root.exists():
        result.errors.append(f"stage directory not found: {stage_root}")
        return result

    stage_slug = infer_stage_slug(stage_root)

    tree_spec = load_yaml(standards_dir / "10_tree_structure.yaml").get("tree_structure", {})
    naming_spec = load_yaml(standards_dir / "20_naming_standards.yaml").get("naming", {})
    validation_spec = load_yaml(standards_dir / "70_validation_rules.yaml").get("validation", {})
    language_spec = load_yaml(standards_dir / "25_language_policy.yaml").get("language_policy", {})

    validate_tree(stage_root, tree_spec, result)
    validate_naming(stage_root, naming_spec, stage_slug, result)
    validate_additional_regex(stage_root, validation_spec, result)
    validate_language(stage_root, language_spec, result)

    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a stage against repository standards")
    parser.add_argument("--standards-dir", default="agent/agents_rules", help="Directory containing standards YAML")
    parser.add_argument("--stage-root", required=True, help="Path to the generated stage root")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    standards_dir = Path(args.standards_dir).resolve()
    stage_root = Path(args.stage_root).resolve()

    result = validate_stage(standards_dir, stage_root)

    if result.errors:
        for msg in result.errors:
            print(f"[error] {msg}")
    if result.warnings:
        for msg in result.warnings:
            print(f"[warn] {msg}")

    if result.ok():
        print("Stage validation passed (OK)")
        return 0

    print(f"Stage validation failed with {len(result.errors)} error(s).")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
