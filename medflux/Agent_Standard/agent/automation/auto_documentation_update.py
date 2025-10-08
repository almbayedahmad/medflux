#!/usr/bin/env python3
"""Update stage-level and main documentation after a stage change."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Iterable, Optional, Tuple

TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
DEFAULT_MAIN_README = "main_documantion/main_readme.md"
DEFAULT_MAIN_CHANGELOG = "main_documantion/main_changelog.md"
DEFAULT_CURRENT_STAGE = "main_documantion/main_current_development_stage.md"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update documentation artefacts after a stage change")
    parser.add_argument("--stage", help="Path to the stage that triggered the update", required=False)
    parser.add_argument("--event", choices=["new", "update", "delete"], default="update", help="Type of change that occurred")
    parser.add_argument("--stage-name", help="Stage name without the phase prefix", required=False)
    parser.add_argument("--phase", help="Phase number (e.g. 03)", required=False)
    parser.add_argument("--changelog", help="Stage changelog to update", default="CHANGELOG.md")
    parser.add_argument("--main-readme", default=DEFAULT_MAIN_README, help="Path to the main README file")
    parser.add_argument("--main-changelog", default=DEFAULT_MAIN_CHANGELOG, help="Path to the main changelog file")
    parser.add_argument("--current-stage", default=DEFAULT_CURRENT_STAGE, help="Path to the current-stage summary file")
    return parser.parse_args(argv)


def derive_stage_metadata(stage_path: Optional[Path], phase_arg: Optional[str], stage_arg: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (identifier, phase, stage_slug)."""
    phase = phase_arg
    stage_slug = stage_arg.lower() if stage_arg else None
    candidate = stage_path.name if stage_path else None

    if candidate and candidate.startswith("phase_"):
        parts = candidate.split("_", 2)
        if len(parts) == 3:
            phase_candidate = parts[1]
            slug_candidate = parts[2]
            phase = phase or phase_candidate
            stage_slug = stage_slug or slug_candidate

    if phase:
        phase = str(phase).zfill(2)
    if stage_slug:
        stage_slug = stage_slug.lower()

    if phase and stage_slug:
        identifier = f"phase_{phase}_{stage_slug}"
    else:
        identifier = candidate or stage_slug

    return identifier, phase, stage_slug


def append_stage_readme_entry(readme_path: Path, change_id: str, stage_id: Optional[str], event: str, timestamp: str) -> bool:
    if not readme_path.exists():
        return False

    text = readme_path.read_text(encoding="utf-8")
    header = "## Change Log"
    entry_header = f"### {change_id}"

    if entry_header in text:
        return False

    lines = text.splitlines()
    if header not in lines:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)
        lines.append("| Stage | Domain | Last Event |")
        lines.append("| ----- | ------ | ---------- |")
        lines.append("")

    if lines and lines[-1].strip():
        lines.append("")

    lines.append(entry_header)
    lines.append(f"- What changed: {event.capitalize()} stage {stage_id or 'unknown stage'} at {timestamp} UTC.")
    if event == 'new':
        why = 'Stage scaffolding created for the product domain.'
        result = 'Stage assets added and documentation initialised.'
    elif event == 'update':
        why = 'Stage assets were modified and documentation must reflect the change.'
        result = 'Stage and main documentation are synchronised with the latest update.'
    elif event == 'delete':
        why = 'Stage retirement requires removing it from the catalog.'
        result = 'Stage references were removed from stage and main documentation.'
    else:
        why = 'Repository activity triggered a documentation refresh.'
        result = 'Documentation updated to match the recorded change.'
    lines.append(f"- Why it was needed: {why}")
    lines.append(f"- Result: {result}")

    readme_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def append_changelog(changelog_path: Path, entry: str, heading: str = "# Changelog") -> bool:
    changelog_path.parent.mkdir(parents=True, exist_ok=True)

    if changelog_path.exists():
        text = changelog_path.read_text(encoding="utf-8")
        if entry in text:
            return False
    else:
        text = heading + "\n\n"

    if heading not in text:
        text = text.rstrip() + f"\n\n{heading}\n\n"

    text = text.rstrip() + f"\n- {entry}\n"
    changelog_path.write_text(text, encoding="utf-8")
    return True


def update_stage_listing(readme_path: Path, stage_id: Optional[str], event: str, timestamp: str, domain: Optional[str]) -> bool:
    if not stage_id:
        return False

    domain_value = domain or "unknown"

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    if readme_path.exists():
        lines = readme_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["# Main Documentation", ""]

    header = "## Managed Stages"
    if header not in lines:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)

    header_idx = lines.index(header)
    section_end = header_idx + 1
    while section_end < len(lines) and not lines[section_end].startswith("## "):
        section_end += 1

    existing = lines[header_idx + 1:section_end]
    entries: dict[str, str] = {}
    for line in existing:
        if line.startswith("| Stage | Domain | Last Event |"):
            continue
        if line.startswith("|") and not line.startswith("| -----"):
            parts = [p.strip() for p in line.strip().strip('|').split('|')]
            if parts:
                entries[parts[0]] = line

    if event == "delete":
        entries.pop(stage_id, None)
    else:
        entries[stage_id] = f"| {stage_id} | {domain_value} | {event} at {timestamp} UTC |"

    rebuilt = ["| Stage | Domain | Last Event |", "| ----- | ------ | ---------- |"]
    for key in sorted(entries):
        rebuilt.append(entries[key])
    rebuilt.append("")

    lines[header_idx + 1:section_end] = rebuilt
    readme_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return True


def update_current_stage(current_stage_path: Path, stage_id: Optional[str], event: str, timestamp: str) -> bool:
    current_stage_path.parent.mkdir(parents=True, exist_ok=True)
    if event == "delete":
        message = f"No active stage. Last removal: {stage_id or 'unknown stage'} at {timestamp} UTC\n"
    else:
        if not stage_id:
            return False
        message = f"{stage_id} - active as of {timestamp} UTC ({event})\n"
    if current_stage_path.exists() and current_stage_path.read_text(encoding="utf-8") == message:
        return False
    current_stage_path.write_text(message, encoding="utf-8")
    return True


def sanitize_path(value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    return Path(value)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime(TIMESTAMP_FMT)

    stage_path = sanitize_path(args.stage)
    if stage_path is not None:
        stage_path = stage_path.resolve()
    stage_id, phase, stage_slug = derive_stage_metadata(stage_path, args.phase, args.stage_name)

    event_label = args.event.lower()
    entry_text = f"{timestamp} UTC - {event_label} stage {stage_id or 'unknown stage'}"
    change_slug = timestamp.replace('-', '').replace(':', '').replace(' ', 'T')
    change_id = f"change-{change_slug}-{event_label}"

    changes_applied = False

    if stage_path and stage_path.exists():
        readme_path = stage_path / "README.md"
        if append_stage_readme_entry(readme_path, change_id, stage_id, event_label, timestamp):
            print(f"Updated {readme_path}")
            changes_applied = True

        changelog_path = Path(args.changelog)
        if not changelog_path.is_absolute() and changelog_path.parent == Path('.'):
            changelog_path = stage_path / changelog_path
        changelog_path = changelog_path.resolve()
        if append_changelog(changelog_path, entry_text):
            print(f"Recorded entry in {changelog_path}")
            changes_applied = True
    elif stage_path:
        print(f"Stage path not found: {stage_path}")

    main_changelog_path = Path(args.main_changelog).resolve()
    if append_changelog(main_changelog_path, entry_text, heading="# Main Changelog"):
        print(f"Recorded entry in {main_changelog_path}")
        changes_applied = True

    domain_value = stage_path.parts[-3] if stage_path and len(stage_path.parts) >= 3 else "unknown"
    if update_stage_listing(Path(args.main_readme).resolve(), stage_id, event_label, timestamp, domain_value):
        print(f"Updated {Path(args.main_readme).resolve()}")
        changes_applied = True

    if update_current_stage(Path(args.current_stage).resolve(), stage_id, event_label, timestamp):
        print(f"Updated {Path(args.current_stage).resolve()}")
        changes_applied = True

    if not changes_applied:
        print("No documentation changes were necessary.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

