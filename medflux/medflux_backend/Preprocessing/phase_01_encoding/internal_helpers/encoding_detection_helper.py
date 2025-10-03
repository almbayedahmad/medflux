from __future__ import annotations

"""Utilities to detect text encoding and convert payloads to UTF-8."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import chardet  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    chardet = None

_UTF8_BOMS = (b"\xef\xbb\xbf",)


@dataclass
class EncodingDetection:
    encoding: Optional[str]
    confidence: Optional[float]
    bom: bool
    is_utf8: bool
    sample_len: int


@dataclass
class EncodingNormalization:
    file_path: str
    normalized_path: Optional[str]
    ok: bool
    reason: Optional[str]
    detected: EncodingDetection


def _has_bom(data: bytes) -> bool:
    return any(data.startswith(bom) for bom in _UTF8_BOMS)


def _normalize_newlines(text: str, policy: str = "lf") -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if policy == "crlf":
        return text.replace("\n", "\r\n")
    return text


def detect_encoding_for_path(path: str, sample_bytes: int = 1024 * 1024) -> EncodingDetection:
    file_path = Path(path)
    if not file_path.exists():
        return EncodingDetection(encoding=None, confidence=None, bom=False, is_utf8=False, sample_len=0)

    data = file_path.read_bytes()
    sample = data[:sample_bytes]
    bom = _has_bom(sample)

    encoding: Optional[str] = None
    confidence: Optional[float] = None

    if chardet is not None and sample:
        try:
            result = chardet.detect(sample) or {}
            encoding = result.get("encoding")
            confidence = result.get("confidence")
        except Exception:  # pragma: no cover - defensive
            encoding = None
            confidence = None

    if encoding:
        normalized = encoding.lower().replace("-", "").replace("_", "")
        if normalized == "ascii":
            encoding = "utf-8"
    else:
        encoding = "utf-8"

    try:
        sample.decode("utf-8")
        is_utf8 = True
    except Exception:
        is_utf8 = False

    return EncodingDetection(
        encoding=encoding,
        confidence=confidence,
        bom=bom,
        is_utf8=is_utf8,
        sample_len=len(sample),
    )


def convert_file_to_utf8(
    path: str,
    *,
    detection: Optional[EncodingDetection] = None,
    dest_path: Optional[str] = None,
    newline_policy: str = "lf",
    errors: str = "strict",
) -> EncodingNormalization:
    file_path = Path(path)
    if detection is None:
        detection = detect_encoding_for_path(path)

    if not file_path.exists():
        return EncodingNormalization(
            file_path=path,
            normalized_path=None,
            ok=False,
            reason="not_found",
            detected=detection,
        )

    encoding = detection.encoding or "utf-8"
    raw = file_path.read_bytes()
    if _has_bom(raw):
        raw = raw[len(_UTF8_BOMS[0]):]

    try:
        text = raw.decode(encoding, errors=errors)
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        text = raw.decode(encoding, errors="replace")

    text = _normalize_newlines(text, newline_policy)

    if dest_path is None:
        stem = file_path.stem or file_path.name
        suffix = file_path.suffix or ".txt"
        dest_path = str(file_path.with_name(f"{stem}.utf8{suffix}"))

    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")

    return EncodingNormalization(
        file_path=path,
        normalized_path=str(dest),
        ok=True,
        reason=None,
        detected=detection,
    )


# Backwards compatibility helpers -------------------------------------------------

def detect_text_encoding(path: str, read_bytes: int = 1024 * 1024) -> EncodingDetection:
    return detect_encoding_for_path(path, sample_bytes=read_bytes)


def convert_to_utf8(
    src_path: str,
    dest_path: Optional[str] = None,
    newline_policy: str = "lf",
    errors: str = "strict",
) -> Dict[str, Any]:
    detection = detect_encoding_for_path(src_path)
    outcome = convert_file_to_utf8(
        src_path,
        detection=detection,
        dest_path=dest_path,
        newline_policy=newline_policy,
        errors=errors,
    )
    return {
        "file_path": outcome.file_path,
        "ok": outcome.ok,
        "normalized_path": outcome.normalized_path,
        "reason": outcome.reason,
        "detected": {
            "encoding": detection.encoding,
            "confidence": detection.confidence,
            "bom": detection.bom,
            "is_utf8": detection.is_utf8,
            "sample_len": detection.sample_len,
        },
    }
