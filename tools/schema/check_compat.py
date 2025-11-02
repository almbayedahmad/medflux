#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = ROOT / "core" / "validation" / "contracts"
VERSION_FILE = ROOT / "core" / "versioning" / "VERSION"


def _run_git(args: List[str]) -> str:
    out = subprocess.check_output(["git", *args], cwd=str(ROOT))
    return out.decode("utf-8", errors="ignore").strip()


def _parse_semver_tag(tag: str) -> Optional[Tuple[int, int, int]]:
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _read_current_version() -> Tuple[int, int, int]:
    v = VERSION_FILE.read_text(encoding="utf-8").strip()
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", v)
    if not m:
        raise RuntimeError(f"Invalid VERSION file: {v}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _previous_release_tag(cur: Tuple[int, int, int]) -> Optional[str]:
    # List tags matching vX.Y.Z and pick the highest strictly less than current
    raw = _run_git(["tag", "--list", "v*"])
    tags = [t for t in raw.splitlines() if t.strip()]
    parsed: List[Tuple[Tuple[int, int, int], str]] = []
    for t in tags:
        sv = _parse_semver_tag(t)
        if sv is None:
            continue
        parsed.append((sv, t))
    if not parsed:
        return None
    parsed.sort(key=lambda x: x[0])
    cur_v = cur
    candidates = [t for (v, t) in parsed if v < cur_v]
    if not candidates:
        return None
    # pick the max less than current
    last = candidates[-1]
    return last


def _git_show(path: str, ref: str) -> Optional[str]:
    try:
        return _run_git(["show", f"{ref}:{path}"])
    except subprocess.CalledProcessError:
        return None


def _git_ls_tree(dir_path: str, ref: str) -> List[str]:
    try:
        out = _run_git(["ls-tree", "-r", "--name-only", ref, dir_path])
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    except subprocess.CalledProcessError:
        return []


def _types(node: Dict[str, Any]) -> Set[str]:
    t = node.get("type")
    if t is None:
        return set()
    if isinstance(t, str):
        return {t}
    if isinstance(t, list):
        return {str(x) for x in t}
    return set()


def _enum(node: Dict[str, Any]) -> Optional[Set[Any]]:
    if "enum" in node and isinstance(node["enum"], list):
        return set(node["enum"])  # type: ignore[return-value]
    return None


def _as_json(text: str) -> Dict[str, Any]:
    return json.loads(text)


def compare_contracts(old: Dict[str, Any], new: Dict[str, Any], rel: str) -> List[Dict[str, Any]]:
    viols: List[Dict[str, Any]] = []
    old_req = set(old.get("required") or [])
    new_req = set(new.get("required") or [])

    # required fields changes
    removed_req = sorted(old_req - new_req)
    added_req = sorted(new_req - old_req)
    if removed_req:
        viols.append({
            "kind": "required_removed",
            "schema": rel,
            "fields": removed_req,
        })
    if added_req:
        viols.append({
            "kind": "required_added",
            "schema": rel,
            "fields": added_req,
        })

    old_props = old.get("properties") or {}
    new_props = new.get("properties") or {}
    if not isinstance(old_props, dict):
        old_props = {}
    if not isinstance(new_props, dict):
        new_props = {}

    # property removals and type/enum narrowing
    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())
    removed_props = sorted(old_keys - new_keys)
    for k in removed_props:
        # If a property was removed, treat as breaking
        viols.append({
            "kind": "property_removed",
            "schema": rel,
            "property": k,
            "required": k in old_req,
        })

    for k in sorted(old_keys & new_keys):
        o = old_props.get(k) or {}
        n = new_props.get(k) or {}
        if not isinstance(o, dict) or not isinstance(n, dict):
            continue
        ot = _types(o)
        nt = _types(n)
        if ot and nt and not ot.issubset(nt):
            viols.append({
                "kind": "type_narrowed",
                "schema": rel,
                "property": k,
                "old_types": sorted(ot),
                "new_types": sorted(nt),
            })
        oe = _enum(o)
        ne = _enum(n)
        if oe is not None and ne is not None and not oe.issubset(ne):
            viols.append({
                "kind": "enum_shrunk",
                "schema": rel,
                "property": k,
                "old_enum": sorted(oe),
                "new_enum": sorted(ne),
            })

    # additionalProperties tightened (from true/omitted to false)
    old_ap = old.get("additionalProperties", True)
    new_ap = new.get("additionalProperties", True)
    if (old_ap is True or old_ap is None) and new_ap is False:
        viols.append({
            "kind": "additional_properties_disabled",
            "schema": rel,
        })

    return viols


def main() -> None:
    # If there's no previous tag, skip (bootstrap)
    cur_v = _read_current_version()
    prev_tag = _previous_release_tag(cur_v)
    if not prev_tag:
        print(json.dumps({"ok": True, "skipped": True, "reason": "no_previous_tag"}))
        return

    # List files at HEAD and at previous tag
    head_files = [p for p in CONTRACTS_DIR.rglob("*.json")]
    tag_rel_files = _git_ls_tree(str(CONTRACTS_DIR.relative_to(ROOT)).replace("\\", "/"), prev_tag)
    tag_files_set = set(tag_rel_files)

    all_violations: List[Dict[str, Any]] = []

    # Compare files present in both
    for p in head_files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if rel not in tag_files_set:
            # new schema file → OK (non-breaking)
            continue
        old_text = _git_show(rel, prev_tag)
        if not old_text:
            continue
        try:
            old = _as_json(old_text)
            new = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": f"failed to load schemas for {rel}: {exc}"}))
            sys.exit(3)
        all_violations.extend(compare_contracts(old, new, rel))

    # Detect removals
    head_rel = {str(p.relative_to(ROOT)).replace("\\", "/") for p in head_files}
    removed = sorted(tag_files_set - head_rel)
    for rel in removed:
        all_violations.append({
            "kind": "schema_removed",
            "schema": rel,
        })

    allowed = False
    # Allow breaking changes if major bumped
    prev_v = _parse_semver_tag(prev_tag)
    if prev_v is not None:
        allowed = cur_v[0] > prev_v[0]

    result = {
        "ok": not all_violations or allowed,
        "prev_tag": prev_tag,
        "current_version": ".".join(map(str, cur_v)),
        "allowed_by_major_bump": allowed,
        "violations": all_violations,
    }
    print(json.dumps(result, ensure_ascii=False))
    if all_violations and not allowed:
        sys.exit(2)


if __name__ == "__main__":
    main()

