#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


SCHEMAS_YAML = Path("core/versioning/schemas.yaml")
MIGRATIONS_DIR = Path("core/versioning/migrations")
MIGRATIONS_MD = Path("core/policy/versioning/MIGRATIONS.md")


def read_schemas() -> str:
    return SCHEMAS_YAML.read_text(encoding="utf-8")


def write_schemas(text: str) -> None:
    SCHEMAS_YAML.write_text(text, encoding="utf-8")


def bump_version(version: str, kind: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not m:
        raise SystemExit(f"Unsupported version format: {version}")
    major, minor, patch = map(int, m.groups())
    if kind == "major":
        return f"{major+1}.0.0"
    if kind == "minor":
        return f"{major}.{minor+1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch+1}"
    raise SystemExit(f"Unknown bump kind: {kind}")


def update_contract_version(yaml_text: str, contract: str, new_version: str) -> str:
    # crude YAML edit: replace line under 'contracts:' matching 'contract: "x.y.z"'
    pattern = re.compile(rf"(^\s*{re.escape(contract)}:\s*\")([0-9]+\.[0-9]+\.[0-9]+)(\")", re.M)
    repl, n = pattern.subn(rf"\g<1>{new_version}\3", yaml_text)
    if n == 0:
        raise SystemExit(f"Contract {contract} not found in schemas.yaml")
    return repl


def next_migration_number() -> int:
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for p in MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.yaml"):
        try:
            n = int(p.name.split("_", 1)[0])
            if n > max_n:
                max_n = n
        except Exception:
            continue
    return max_n + 1


def write_migration_file(n: int, contract: str, old: str, new: str) -> Path:
    fname = f"{n:03d}_{contract}_{old}_to_{new}.yaml"
    path = MIGRATIONS_DIR / fname
    body = (
        f"# Migration {n:03d}: {contract} {old} -> {new}\n"
        f"id: {n:03d}_{contract}_{old}_to_{new}\n"
        f"schema: {contract}\nfrom: {old}\n" + f"to: {new}\n"
        f"date: {dt.date.today().isoformat()}\nsteps:\n  - action: bump\n    description: Bump {contract} schema from {old} to {new}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def append_migrations_md(contract: str, new: str, description: str = "Schema bump") -> None:
    MIGRATIONS_MD.parent.mkdir(parents=True, exist_ok=True)
    if not MIGRATIONS_MD.exists():
        MIGRATIONS_MD.write_text("# Migrations Summary\n| Version | Schema | Description | Date |\n|----------|---------|-------------|------|\n", encoding="utf-8")
    line = f"| v{new} | {contract} {new} | {description} | {dt.date.today().isoformat()} |\n"
    with MIGRATIONS_MD.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> None:
    ap = argparse.ArgumentParser(description="Bump a contract version and create migration entry")
    ap.add_argument("contract", help="contract name (e.g., stage_contract)")
    ap.add_argument("kind", choices=["major", "minor", "patch"], help="which version part to bump")
    args = ap.parse_args()

    text = read_schemas()
    m = re.search(rf"^\s*{re.escape(args.contract)}:\s*\"([0-9]+\.[0-9]+\.[0-9]+)\"", text, re.M)
    if not m:
        raise SystemExit(f"Cannot find version for contract {args.contract}")
    old = m.group(1)
    new = bump_version(old, args.kind)
    updated = update_contract_version(text, args.contract, new)
    write_schemas(updated)
    n = next_migration_number()
    mf = write_migration_file(n, args.contract, old, new)
    append_migrations_md(args.contract, new)
    print(f"Bumped {args.contract} {old} -> {new}; migration: {mf}")


if __name__ == "__main__":
    main()
