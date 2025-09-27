import os
from typing import Optional
from .encoding_detector import detect_text_encoding, _has_bom

def _normalize_newlines(text: str, policy: str = "lf") -> str:
    # policy: "lf" -> "\n", "crlf" -> "\r\n"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if policy == "crlf":
        return text.replace("\n", "\r\n")
    return text  # lf

def convert_to_utf8(src_path: str,
                    dest_path: Optional[str] = None,
                    newline_policy: str = "lf",
                    errors: str = "strict") -> dict:
    """
    Convert the text file to UTF-8 without a BOM and normalise line endings.
    - newline_policy: "lf" or "crlf"
    - errors: "strict" / "replace" / "ignore"
    """
    info = detect_text_encoding(src_path)
    if not os.path.exists(src_path):
        return {
            "file_path": src_path,
            "ok": False,
            "reason": "not_found",
            "detected": info.__dict__,
        }

    enc = info.encoding or "utf-8"
    if dest_path is None:
        base, ext = os.path.splitext(src_path)
        dest_path = f"{base}.utf8{ext or '.txt'}"

    with open(src_path, "rb") as f:
        raw = f.read()

    # Remove the BOM when present
    if _has_bom(raw):
        raw = raw[3:]

    # Decode the raw bytes using the detected encoding
    try:
        text = raw.decode(enc, errors=errors)
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        text = raw.decode(enc, errors="replace")

    # Normalise line endings according to the requested policy
    text = _normalize_newlines(text, policy=newline_policy)

    # Write UTF-8 output without a BOM
    with open(dest_path, "wb") as f:
        f.write(text.encode("utf-8"))

    return {
        "file_path": src_path,
        "ok": True,
        "normalized_path": dest_path,
        "detected": info.__dict__,
    }


