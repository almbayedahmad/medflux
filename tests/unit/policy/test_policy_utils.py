from __future__ import annotations

from pathlib import Path

import pytest

import core.policy_utils as putil


@pytest.mark.unit
def test_get_policy_path_missing_raises() -> None:
    with pytest.raises(FileNotFoundError):
        putil.get_policy_path("does/not/exist.yaml")


@pytest.mark.unit
def test_load_policy_with_overrides_merges(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Build a fake repo with base policy and overrides
    repo = tmp_path
    base = repo / "core" / "policy" / "validation"
    base.mkdir(parents=True)
    (repo / "core" / "policy").mkdir(parents=True, exist_ok=True)
    (repo / "core" / "policy" / "rules.local.yaml").write_text(
        "demotions:\n  by_validator: ['additionalProperties']\n  foo: bar\n",
        encoding="utf-8",
    )
    (base / "validation_rules.yaml").write_text(
        "demotions:\n  by_validator: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(putil, "repo_root", lambda: repo)
    data = putil.load_policy_with_overrides("validation/validation_rules.yaml")
    assert isinstance(data, dict)
    # Ensure override merged
    assert data.get("demotions", {}).get("by_validator") == ["additionalProperties"]
