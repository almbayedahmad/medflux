from __future__ import annotations

from core.preprocessing.cross_phase.helpers.main_pre_helpers_lang_detect import (
    compute_language_hint as compute_readers_language_hint,
    compute_locale_hint as compute_readers_locale_hint,
    compute_merged_language_hint as compute_readers_merged_language_hint,
)


def test_compute_readers_language_hint_mixed_scores() -> None:
    text = "Das Krankenhaus hospital betreut Patienten and patients"
    assert compute_readers_language_hint(text) == "mixed"


def test_compute_readers_locale_hint_detects_de_format() -> None:
    text = "Rechnung vom 12.03.2024 ueber 1.200,00 EUR"
    assert compute_readers_locale_hint(text) in {"de", "mixed"}


def test_compute_readers_merged_language_hint_prefers_existing() -> None:
    assert compute_readers_merged_language_hint("de", "unknown") == "de"
    assert compute_readers_merged_language_hint("unknown", "en") == "en"
    assert compute_readers_merged_language_hint("de", "en") == "mixed"
