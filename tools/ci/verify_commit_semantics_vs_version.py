#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[.-].+)?$")


def read_file_version() -> str:
    with open("core/versioning/VERSION", "r", encoding="utf-8") as f:
        return f.read().strip()


def get_base_ref() -> str | None:
    base = os.environ.get("GITHUB_BASE_REF")
    if not base:
        return None
    try:
        subprocess.check_call(["git", "fetch", "origin", base], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return f"origin/{base}"


def get_merge_base(base_ref: str | None) -> str:
    if base_ref:
        try:
            out = subprocess.check_output(["git", "merge-base", "HEAD", base_ref], stderr=subprocess.DEVNULL)
            return out.decode("utf-8").strip()
        except Exception:
            pass
    # Fallback to previous commit
    out = subprocess.check_output(["git", "rev-parse", "HEAD^"], stderr=subprocess.DEVNULL)
    return out.decode("utf-8").strip()


def read_prev_version(base_commit: str) -> str | None:
    try:
        out = subprocess.check_output(["git", "show", f"{base_commit}:core/versioning/VERSION"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None


def version_bump_kind(old: str, new: str) -> str:
    mo = SEMVER_RE.match(old) if old else None
    mn = SEMVER_RE.match(new)
    if not mn:
        return "unknown"
    omaj, omin, opat = (map(int, mo.groups()) if mo else (0, 0, 0))
    nmaj, nmin, npat = map(int, mn.groups())
    if nmaj > omaj:
        return "major"
    if nmin > omin:
        return "minor"
    if npat > opat:
        return "patch"
    return "none"


def main() -> None:
    base_ref = get_base_ref()
    base = get_merge_base(base_ref)
    old = read_prev_version(base) or "0.0.0"
    new = read_file_version()
    kind = version_bump_kind(old, new)

    # Gather commit messages in range base..HEAD
    try:
        out = subprocess.check_output(["git", "log", "--pretty=%s", f"{base}..HEAD"], stderr=subprocess.DEVNULL)
        messages = out.decode("utf-8").splitlines()
    except Exception:
        messages = []

    requires_major = any(m.startswith("feat!") or "BREAKING CHANGE" in m for m in messages)
    requires_minor = any(m.startswith("feat:") for m in messages)

    ok = True
    if requires_major and kind not in {"major"}:
        print(f"ERROR: commits indicate a major bump but version is {new} (from {old})", file=sys.stderr)
        ok = False
    if (not requires_major and requires_minor) and kind not in {"major", "minor"}:
        print(f"ERROR: commits indicate a minor bump but version is {new} (from {old})", file=sys.stderr)
        ok = False

    if not ok:
        sys.exit(1)
    print(f"OK: commits match version bump {old} -> {new} ({kind})")


if __name__ == "__main__":
    main()
