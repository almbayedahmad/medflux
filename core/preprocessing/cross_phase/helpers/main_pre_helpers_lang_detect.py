from __future__ import annotations

"""Generic language detection utilities for all preprocessing phases."""

import re
from typing import Optional, Set

DE_TRIGGER_CHARS: Set[str] = {"ue", "oe", "ae", "ss"}
DE_KEYWORDS = {
    "und",
    "der",
    "die",
    "das",
    "ein",
    "eine",
    "ist",
    "nicht",
    "mit",
    "fuer",
    "aus",
    "dem",
    "den",
    "des",
    "bei",
    "oder",
    "wir",
    "sie",
    "dass",
    "zum",
    "zur",
    "ueber",
}
EN_KEYWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "your",
    "you",
    "please",
    "dear",
    "hello",
    "thank",
    "invoice",
    "date",
    "page",
    "tax",
}
DATE_KEYWORDS_DE = {
    "januar",
    "februar",
    "maerz",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "dezember",
}
DATE_KEYWORDS_EN = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}


def compute_language_hint(text: str) -> str:
    """Return a coarse language label for the provided text."""

    if not text:
        return "unknown"
    normalized = re.sub(r"[^A-Za-z0-9 ]", " ", text).lower()
    tokens = [tok for tok in normalized.split() if tok]
    if not tokens:
        return "unknown"
    de_scores = sum(
        1
        for tok in tokens
        if tok in DE_KEYWORDS or any(marker in tok for marker in DE_TRIGGER_CHARS)
    )
    en_scores = sum(1 for tok in tokens if tok in EN_KEYWORDS)
    if any(tok in DATE_KEYWORDS_DE for tok in tokens):
        de_scores += 1
    if any(tok in DATE_KEYWORDS_EN for tok in tokens):
        en_scores += 1
    if de_scores == 0 and en_scores == 0:
        return "unknown"
    if de_scores > 0 and en_scores > 0 and abs(de_scores - en_scores) <= 1:
        return "mixed"
    return "de" if de_scores > en_scores else "en"


def compute_locale_hint(text: str) -> str:
    """Return a locale hint derived from number/date formats found in text."""

    if not text:
        return "unknown"
    has_de = bool(re.search(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", text))
    has_en = bool(re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text))
    if re.search(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", text):
        has_de = True
    if re.search(r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b", text):
        has_en = True
    if has_de and has_en:
        return "mixed"
    if has_de:
        return "de"
    if has_en:
        return "en"
    return "unknown"


def compute_merged_language_hint(existing: Optional[str], new_hint: str) -> str:
    """Combine two language hints using the legacy heuristic."""

    new_hint = new_hint or "unknown"
    if not existing or existing == "unknown":
        return new_hint
    if new_hint == "unknown":
        return existing
    if new_hint == existing:
        return existing
    return "mixed"


# Backwards-compatible aliases for readers stage
compute_readers_language_hint = compute_language_hint
compute_readers_locale_hint = compute_locale_hint
compute_readers_merged_language_hint = compute_merged_language_hint


__all__ = [
    "compute_language_hint",
    "compute_locale_hint",
    "compute_merged_language_hint",
    # Backwards-compatible aliases for readers stage
    "compute_readers_language_hint",
    "compute_readers_locale_hint",
    "compute_readers_merged_language_hint",
]
