#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _type_of(node: Dict[str, Any]) -> str:
    t = node.get("type")
    if isinstance(t, list):
        return "/".join(str(x) for x in t)
    if isinstance(t, str):
        return t
    if "$ref" in node:
        return "ref"
    if "const" in node:
        return f"const={node['const']}"
    return "object"


def _summarize_defs(defs: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for name, node in defs.items():
        if not isinstance(node, dict):
            continue
        t = _type_of(node)
        lines.append(f"  - `$defs.{name}`: {t}")
    return lines


def _summarize_props(props: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for k, v in props.items():
        if not isinstance(v, dict):
            lines.append(f"  - `{k}`: object")
            continue
        t = _type_of(v)
        extra = []
        if "enum" in v:
            try:
                extra.append("enum=" + ",".join(map(str, v["enum"])) )
            except Exception:
                pass
        if "format" in v:
            extra.append(f"format={v['format']}")
        if "const" in v:
            extra.append(f"const={v['const']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        lines.append(f"  - `{k}`: {t}{suffix}")
    return lines


def _summarize_schema(path: Path, sch: Dict[str, Any]) -> str:
    title = sch.get("title") or path.stem
    sid = sch.get("$id", "")
    req = sch.get("required") or []
    props = sch.get("properties") or {}
    defs = sch.get("$defs") or {}
    lines: List[str] = []
    lines.append(f"### {title}")
    if sid:
        lines.append(f"- id: `{sid}`")
    lines.append(f"- file: `{path.as_posix()}`")
    if req:
        lines.append(f"- required: {', '.join(str(x) for x in req)}")
    if isinstance(props, dict) and props:
        lines.append("- properties:")
        lines.extend(_summarize_props(props))
    if isinstance(defs, dict) and defs:
        lines.append("- defs:")
        lines.extend(_summarize_defs(defs))
    lines.append("")
    return "\n".join(lines)


def build_docs(root: Path) -> str:
    docs: List[str] = ["# Validation Schemas", ""]
    for p in sorted(root.rglob("*.json")):
        try:
            sch = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(sch, dict):
            continue
        docs.append(_summarize_schema(p, sch))
    return "\n".join(docs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Markdown docs for validation schemas")
    parser.add_argument("--root", default="core/validation/contracts", help="Schemas root directory")
    parser.add_argument("--out", default="core/validation/SCHEMAS.md", help="Output Markdown file")
    parser.add_argument("--check", action="store_true", help="Check if output is up-to-date; exit 1 if differs")
    args = parser.parse_args()

    root = Path(args.root)
    out_path = Path(args.out)
    content = build_docs(root)
    if args.check:
        existing = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        if existing != content:
            print("Schema docs are out-of-date. Run: python tools/schema/generate_schema_docs.py", file=sys.stderr)
            sys.exit(1)
        print("Schema docs OK")
        return
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
