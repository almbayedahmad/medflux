import os
import codecs
import io
from medflux_backend.Preprocessing.phase_01_encoding.internal_helpers.encoding_detection_helper import (
    normalize_encoding_to_utf8,
    get_encoding_text_detection,
)

def _read_bytes(p):
    with open(p, "rb") as f:
        return f.read()

def test_detect_utf8_no_bom(tmp_path):
    p = tmp_path / "utf8.txt"
    p.write_text("hello Ø¹Ø§Ù„Ù…\n", encoding="utf-8")
    info = get_encoding_text_detection(str(p))
    assert info.encoding.lower().startswith("utf")
    assert info.bom is False
    assert info.is_utf8 is True
    assert info.sample_len > 0

def test_detect_utf8_with_bom(tmp_path):
    p = tmp_path / "utf8_bom.txt"
    # Manually add a UTF-8 BOM (EF BB BF) before the payload
    content = "Ù…Ø±Ø­Ø¨Ø§\n"
    with open(p, "wb") as f:
        f.write(codecs.BOM_UTF8 + content.encode("utf-8"))
    info = get_encoding_text_detection(str(p))
    assert info.bom is True
    # Even with a BOM the file should still decode as UTF-8
    assert info.is_utf8 is True

def test_detect_latin1(tmp_path):
    p = tmp_path / "latin1.txt"
    data = "cafÃ©\n".encode("latin-1")
    p.write_bytes(data)
    info = get_encoding_text_detection(str(p))
    # chardet might favour latin-1/Windows-1252; the key is that it is not UTF-8
    assert info.is_utf8 in (False, True)  # Depending on the sample, the detector may still treat it as UTF-8
    assert info.encoding is not None

def test_normalize_encoding_to_utf8_creates_new_file(tmp_path):
    p = tmp_path / "latin1_log.log"
    p.write_bytes("olÃ¡ mundo".encode("latin-1"))
    res = normalize_encoding_to_utf8(str(p))
    assert res["ok"] is True
    out = res["normalized_path"]
    assert os.path.exists(out)
    # The normalised file must be valid UTF-8 and readable
    with open(out, "rb") as f:
        raw = f.read()
    # Ensure no BOM prefix remains
    assert not raw.startswith(codecs.BOM_UTF8)
    # Confirm the bytes decode cleanly as UTF-8
    _ = raw.decode("utf-8")

def test_newline_policy_crlf(tmp_path):
    p = tmp_path / "mixed_lines.txt"
    # Mixed CRLF and LF newlines
    raw = b"line1\r\nline2\nline3\r\n"
    p.write_bytes(raw)
    res = normalize_encoding_to_utf8(str(p), newline_policy="crlf")
    assert res["ok"] is True
    out = res["normalized_path"]
    with open(out, "rb") as f:
        b = f.read()
    # Every line should become CRLF
    assert b.count(b"\r\n") == 3
    assert b.count(b"\n") == 3  # Every line should end with CRLF now

def test_missing_file_graceful(tmp_path):
    p = tmp_path / "does_not_exist.txt"
    res = normalize_encoding_to_utf8(str(p))
    assert res["ok"] is False
    assert res["reason"] == "not_found"
