import os
from typing import Optional, Dict
from dataclasses import dataclass

# Attempt to use chardet; fall back gracefully if it is missing
try:
    import chardet
except Exception:
    chardet = None

UTF8_BOMS = [b"\xef\xbb\xbf"]

def _has_bom(data: bytes) -> bool:
    return any(data.startswith(bom) for bom in UTF8_BOMS)

@dataclass
class DetectionInfo:
    encoding: Optional[str]
    confidence: Optional[float]
    bom: bool
    is_utf8: bool
    sample_len: int

def detect_text_encoding(path: str, read_bytes: int = 1024 * 1024) -> DetectionInfo:
    if not os.path.exists(path):
        return DetectionInfo(None, None, False, False, 0)

    with open(path, "rb") as f:
        data = f.read(read_bytes)

    bom = _has_bom(data)
    enc: Optional[str] = None
    conf: Optional[float] = None

    if chardet is not None:
        try:
            res = chardet.detect(data) or {}
            enc = res.get("encoding")
            conf = res.get("confidence")
        except Exception:
            enc, conf = None, None

    # Normalise the chardet result
    if enc:
        en = enc.lower().replace("-", "").replace("_", "")
        if en in ("ascii",):
            enc = "utf-8"  # ASCII is compatible with UTF-8
    else:
        enc = "utf-8"  # fallback default when detection fails

    # Verify whether the bytes actually decode as UTF-8
    try:
        data.decode("utf-8")
        is_utf8 = True
    except Exception:
        is_utf8 = False

    return DetectionInfo(encoding=enc, confidence=conf, bom=bom, is_utf8=is_utf8, sample_len=len(data))


