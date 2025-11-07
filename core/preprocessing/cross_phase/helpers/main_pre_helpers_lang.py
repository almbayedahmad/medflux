"""Cross-phase helpers for normalising high-level language signals.

These utilities are shared by encoding/readers phases so they live in
`main_pre_helpers` rather than inside any one phase.
"""

from typing import Dict
import re


def normalise_lang(tag: str) -> str:
    """Collapse a raw language tag into the canonical two-letter form."""

    t = (tag or "").lower().strip()
    if t in ("de", "ger", "deu"):
        return "de"
    if t in ("en", "eng"):
        return "en"
    return t


def collapse_doc_lang(doc_share: Dict[str, float]) -> str:
    """Summarise a per-language ratio map into a coarse-grained label."""

    de = doc_share.get("de", 0.0)
    en = doc_share.get("en", 0.0)
    if de > 0.8 and en < 0.2:
        return "de"
    if en > 0.8 and de < 0.2:
        return "en"
    return "de+en"


def tokenise_langs(text: str) -> Dict[str, int]:
    """Return a naive token count split between ASCII vs non-ASCII tokens."""

    toks = re.findall(r"\w+", text or "")
    en = sum(1 for token in toks if token.isascii())
    de = max(len(toks) - en, 0)
    return {"de": de, "en": en}
