#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_builder_v2.py
-------------------
Generate a stage directly from the standards directory and the template bundle
without relying on an intermediate architect_standard.yaml file.

Features:
- Loads and merges standards/*.yaml (tree/naming/contract/generation/validation).
- Reads the manifest (YAML) to determine phase_number, stage_name, features, and generate flags.
- Applies naming rules from naming_standards.yaml (when present) with a default role map.
- Renders .tpl templates by replacing {{placeholders}}.
- Supports --dry-run, --force, --verbose, and optional --validate execution modes.

Usage:
  python stage_builder_v2.py     --manifest automated_operations/stage_builder/example_manifest.yaml     --standards-dir Agent_Standard/standards     --templates automated_operations/stage_builder/templates     --base-dir products/my_product     --domain ingestion     --dry-run --verbose --validate
"""
from __future__ import annotations

import argparse, sys, re, subprocess
from pathlib import Path

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def eprint(*a, **k):
    print(*a, file=sys.stderr, **k)

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str, *, force: bool=False):
    if p.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


# -----------------------------------------------------------------------------
# YAML loader (with graceful error if PyYAML missing)
# -----------------------------------------------------------------------------

def load_yaml_text(txt: str):
    try:
        import yaml
    except Exception as ex:
        raise RuntimeError(
            "PyYAML is not available. Install it with: pip install pyyaml"
        ) from ex
    return yaml.safe_load(txt) or {}

def load_yaml_file(path: Path):
    return load_yaml_text(read_text(path))

# -----------------------------------------------------------------------------
# Standards composition
# -----------------------------------------------------------------------------

def compose_standards(standards_dir: Path) -> dict:
    """
    Read every YAML file in the standards directory and assemble a composite mapping.
    Attempt to detect each section by name or well-known keys.
    """
    if not standards_dir.exists():
        raise FileNotFoundError(f"Standards directory not found: {standards_dir}")

    parts: dict[str, dict] = {}
    for y in sorted(standards_dir.glob("*.yaml")):
        data = load_yaml_file(y) or {}
        name = y.name
        # Heuristic section detection
        if "tree" in data or name.startswith("10_"):
            parts["tree"] = data
        if "naming" in data or name.startswith("20_"):
            parts["naming"] = data
        if "contract" in data or name.startswith("30_"):
            parts["contract"] = data
        if "generation" in data or name.startswith("40_"):
            parts["generation"] = data
        if "validation" in data or name.startswith("70_"):
            parts["validation"] = data
        # Store any additional sections we discover
        stem = y.stem
        if stem not in parts:
            parts[stem] = data

    arch = {
        "meta": {"version": 2, "id": "architect_standard_direct"},
        "tree": parts.get("tree", {}),
        "naming": parts.get("naming", {}),
        "contract": parts.get("contract", {}),
        "generation": parts.get("generation", {}),
        "validation": parts.get("validation", {}),
        "all_parts": parts,
    }
    return arch

# -----------------------------------------------------------------------------
# Naming helpers
# -----------------------------------------------------------------------------

DEFAULT_ROLE_FILES = {
    # role -> filename pattern (with <stage> placeholder)
    "pipeline": "<stage>_pipeline.py",
    "config_connector": "<stage>_config_connector.py",
    "upstream_connector": "<stage>_upstream_connector.py",
    "normalize": "<stage>_normalize.py",
    "deduplicate": "<stage>_deduplicate.py",
    "textnorm": "<stage>_textnorm.py",
    "indexing": "<stage>_indexing.py",
    "package_init": "__init__.py",
    "config_yaml": "<stage>.yaml",
    "config_schema": "schema_<stage>.yaml",
    "config_meta": "<stage>.meta.yaml",
    "schema_types": "<stage>_types.py",
    "output": "<stage>_output.py",  # output module uses the stage-prefixed name
    # tests
    "test_config": "test_<stage>_config.py",
    "test_integration": "test_<stage>_integration_pipeline.py",
}

def stage_dir_name(phase_number: str, stage_name: str) -> str:
    return f"phase_{int(phase_number):02d}_{stage_name}"

def apply_stage_placeholder(name_pattern: str, stage: str) -> str:
    return name_pattern.replace("<stage>", stage)

def enforce_file_regex(naming: dict, stage: str, filename: str):
    """
    Validate against naming rules when regex patterns are provided.
    """
    file_pat = naming.get("naming", {}).get("file_name_pattern")
    must_prefix = naming.get("naming", {}).get("must_start_with_stage_prefix", False)
    prefix_placeholder = naming.get("naming", {}).get("stage_prefix_placeholder", "<stage>_")
    if file_pat:
        if not re.match(file_pat, filename):
            raise ValueError(f"Filename does not satisfy naming pattern ({file_pat}): {filename}")
    if must_prefix:
        expected = prefix_placeholder.replace("<stage>", stage)
        if not filename.startswith(expected):
            # Some files may intentionally diverge; relax enforcement when policy allows it.
            # Remove this exception if stricter validation is required.
            pass

# -----------------------------------------------------------------------------
# Template rendering (very simple {{var}} replacement)
# -----------------------------------------------------------------------------

def render_template(txt: str, ctx: dict) -> str:
    out = txt
    for k, v in ctx.items():
        pattern = re.compile(r"{{\s*" + re.escape(k) + r"\s*}}")
        out = pattern.sub(str(v), out)
    return out


def invoke_validator(stage_dir: Path, standards_dir: Path, verbose: bool) -> None:
    validator_path = Path(__file__).resolve().parent.parent / "validation_op" / "standards_validator.py"
    cmd = [sys.executable, str(validator_path), "--stage-root", stage_dir.as_posix()]
    if standards_dir:
        cmd.extend(["--standards-dir", standards_dir.as_posix()])
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError("Validator reported failures; inspect the output above.")
    if verbose:
        print("Validator finished with no errors.")

# -----------------------------------------------------------------------------
# Build plan
# -----------------------------------------------------------------------------

def build_plan(manifest: dict, arch: dict, templates_root: Path, base_dir: Path, domain: str, verbose: bool=False) -> dict:
    """
    Prepare the generation plan (source templates -> destination paths) using the manifest, standards, and templates.
    """
    phase_value = manifest.get("phase_number", "00")
    phase = str(phase_value).zfill(2)

    raw_stage = str(manifest.get("stage_name", "stage")).strip()
    slug_candidate = re.sub(r"[^a-z0-9_]+", "_", raw_stage.lower())
    stage = re.sub(r"_+", "_", slug_candidate).strip("_") or "stage"
    stage_title = re.sub(r"[_\-]+", " ", raw_stage).strip().title() or stage.replace("_", " ").title()

    features = manifest.get("features", {}) or {}
    generate = manifest.get("generate", {}) or {}

    stage_dir_name_value = stage_dir_name(phase, stage)
    stage_dir = base_dir / domain / stage_dir_name_value

    # Select templates based on feature and generate flags
    # Expected template layout:
    # templates/
    #   root/ (README, Makefile, CHANGELOG, stageignore ...)
    #   pipeline/ entry.py.tpl  -> pipeline file
    #   connectors/ config_conn.py.tpl, upstream_conn.py.tpl -> connectors
    #   core/ normalize.py.tpl, deduplicate.py.tpl -> processors
    #   helpers/ textnorm.py.tpl, indexing.py.tpl -> helpers
    #   outputs/ output.py.tpl
    #   tests/ test_config.py.tpl, test_integration.py.tpl
    plan = []

    ctx = {
        "phase": phase,
        "phase_number": phase,
        "stage": stage,
        "stage_name": stage,
        "stage_slug": stage,
        "stage_original": raw_stage,
        "StageName": stage_title,
        "stage_title": stage_title,
        "stage_dir": stage_dir.as_posix(),
        "stage_dir_name": stage_dir_name_value,
        "domain": domain,
        "base_dir": base_dir.as_posix(),
    }

    def add_from_dir(subdir: str, mapping: list[tuple[str, str]]):
        tdir = templates_root / subdir
        for tpl_name, role in mapping:
            tpl_path = tdir / tpl_name
            if not tpl_path.exists():
                continue
            # Determine the output filename
            pattern = DEFAULT_ROLE_FILES.get(role, f"{role}.py")
            out_name = apply_stage_placeholder(pattern, stage)
            # Enforce naming policy when available
            try:
                if Path(out_name).suffix == ".py":
                    enforce_file_regex(arch.get("naming", {}), stage, out_name)
            except Exception as ex:
                if verbose:
                    eprint(f"[naming] warning: {ex}")
            # Destination path
            # Map roles to their expected subdirectories
            if subdir == "root":
                out_path = stage_dir / out_name  # Root files often are not Python modules
            elif subdir == "pipeline":
                out_path = stage_dir / "pipeline_workflow" / out_name
            elif subdir == "config":
                out_path = stage_dir / "config" / out_name
            elif subdir == "connectors":
                out_path = stage_dir / "connecters" / out_name
            elif subdir == "core":
                out_path = stage_dir / "core_processors" / out_name
            elif subdir == "helpers":
                out_path = stage_dir / "internal_helpers" / out_name
            elif subdir == "schemas":
                out_path = stage_dir / "schemas" / out_name
            elif subdir == "outputs":
                out_path = stage_dir / "outputs" / out_name
            elif subdir == "tests":
                out_path = stage_dir / "tests" / out_name
            else:
                out_path = stage_dir / out_name

            plan.append((tpl_path, out_path))

    # configuration files
    if (templates_root / "config").exists() and generate.get("config", True):
        add_from_dir("config", [
            ("stage.yaml.tpl", "config_yaml"),
            ("stage_schema.yaml.tpl", "config_schema"),
            ("stage.meta.yaml.tpl", "config_meta"),
        ])

    if (templates_root / "schemas").exists() and generate.get("schemas", True):
        add_from_dir("schemas", [
            ("__init__.py.tpl", "package_init"),
            ("types.py.tpl", "schema_types"),
        ])

    # root files (README/Makefile/CHANGELOG/stageignore)
    root_dir = templates_root / "root"
    if root_dir.exists() and (generate.get("root", True)):
        # Root files reuse the template names (without .tpl)
        for tpl in sorted(root_dir.glob("*.tpl")):
            # Strip the .tpl suffix to recover the target filename
            out_name = tpl.name.replace(".tpl", "")
            # Root-level files are exempt from stage_* naming rules
            out_path = stage_dir / out_name
            plan.append((tpl, out_path))

    # pipeline
    if (templates_root / "pipeline").exists() and generate.get("pipeline", True):
        add_from_dir("pipeline", [("entry.py.tpl", "pipeline"), ("__init__.py.tpl", "package_init")])

    # connectors
    if (templates_root / "connectors").exists() and generate.get("connectors", True):
        add_from_dir("connectors", [
            ("config_conn.py.tpl", "config_connector"),
            ("upstream_conn.py.tpl", "upstream_connector"),
            ("__init__.py.tpl", "package_init"),
        ])

    # core processors (respect features)
    if (templates_root / "core").exists() and generate.get("core", True):
        add_from_dir("core", [("__init__.py.tpl", "package_init")])
        if features.get("normalization", True):
            add_from_dir("core", [("normalize.py.tpl", "normalize")])
        if features.get("deduplication", False):
            add_from_dir("core", [("deduplicate.py.tpl", "deduplicate")])

    # helpers
    if (templates_root / "helpers").exists() and generate.get("helpers", True):
        add_from_dir("helpers", [("__init__.py.tpl", "package_init")])
        if features.get("schemas", False):
            add_from_dir("helpers", [("textnorm.py.tpl", "textnorm")])
        if features.get("indexing", False):
            add_from_dir("helpers", [("indexing.py.tpl", "indexing")])

    # outputs
    if (templates_root / "outputs").exists() and generate.get("outputs", True):
        add_from_dir("outputs", [("output.py.tpl", "output"), ("__init__.py.tpl", "package_init")])

    # tests
    if (templates_root / "tests").exists() and generate.get("tests", True):
        add_from_dir("tests", [
            ("__init__.py.tpl", "package_init"),
            ("test_config.py.tpl", "test_config"),
            ("test_integration.py.tpl", "test_integration"),
        ])

    return {
        "ctx": ctx,
        "stage_dir": stage_dir,
        "items": plan,
    }

# -----------------------------------------------------------------------------
# Main build
# -----------------------------------------------------------------------------

def run_builder(manifest_path: Path, standards_dir: Path, templates_root: Path, base_dir: Path, domain: str, dry_run: bool, force: bool, verbose: bool, validate: bool):
    arch = compose_standards(standards_dir)
    manifest = load_yaml_file(manifest_path)
    plan = build_plan(manifest, arch, templates_root, base_dir, domain, verbose=verbose)

    if verbose or dry_run:
        import json
        print(json.dumps({
            "stage_dir": plan["stage_dir"].as_posix(),
            "ctx": plan["ctx"],
            "files": [{"from": str(src), "to": str(dst)} for (src, dst) in plan["items"]]
        }, ensure_ascii=False, indent=2))

    if dry_run:
        return

    # Ensure required directories exist even if no files are generated
    required_dirs = arch.get("tree", {}).get("required_subfolders", [])
    for folder in required_dirs:
        (plan["stage_dir"] / folder).mkdir(parents=True, exist_ok=True)

    # Execute the plan: render each template and write the target file
    for src, dst in plan["items"]:
        txt = read_text(src)
        rendered = render_template(txt, plan["ctx"])
        try:
            write_text(dst, rendered, force=force)
            if verbose:
                print(f"[write] {dst}")
        except FileExistsError as ex:
            eprint(f"[skip] {ex}")

    if validate:
        invoke_validator(plan["stage_dir"], standards_dir, verbose)

    # Ensure a minimal README exists in the generated stage directory
    readme = plan["stage_dir"] / "README.md"
    if not readme.exists():
        intro = (
            f"# Stage: {plan['ctx']['StageName']} (Phase {plan['ctx']['phase']})\n\n"
            f"- Domain: {domain}\n"
            f"- Base: {base_dir}\n"
        )
        write_text(readme, intro, force=True)

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description="Direct Standards+Templates Stage Builder")
    ap.add_argument("--manifest", required=True, help="Path to manifest YAML")
    ap.add_argument("--standards-dir", required=True, help="Path to standards/ directory")
    ap.add_argument("--templates", required=True, help="Path to templates/ root")
    ap.add_argument("--base-dir", required=True, help="Base product dir (e.g., products/my_product)")
    ap.add_argument("--domain", required=True, help="Domain root (e.g., ingestion)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--validate", action="store_true", help="Run standards validator after generation")
    return ap.parse_args()

def main():
    args = parse_args()
    run_builder(
        manifest_path=Path(args.manifest),
        standards_dir=Path(args.standards_dir),
        templates_root=Path(args.templates),
        base_dir=Path(args.base_dir),
        domain=args.domain,
        dry_run=args.dry_run,
        force=args.force,
        verbose=args.verbose,
        validate=args.validate,
    )

if __name__ == "__main__":
    main()
