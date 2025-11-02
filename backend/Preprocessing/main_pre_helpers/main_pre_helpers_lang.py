from typing import Dict, List


def normalise_lang(tag: str) -> str:
    t = (tag or "").lower().strip()
    if t in ("de","ger","deu"): return "de"
    if t in ("en","eng"): return "en"
    return t


def collapse_doc_lang(doc_share: Dict[str, float]) -> str:
    de = doc_share.get("de", 0.0); en = doc_share.get("en", 0.0)
    if de > 0.8 and en < 0.2: return "de"
    if en > 0.8 and de < 0.2: return "en"
    return "de+en"


def tokenise_langs(text: str) -> Dict[str, int]:
    import re
    toks = re.findall(r"\w+", text or "")
    en = sum(1 for t in toks if t.isascii())
    de = max(len(toks) - en, 0)
    return {"de": de, "en": en}
