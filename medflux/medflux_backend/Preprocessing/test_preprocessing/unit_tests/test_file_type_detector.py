from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type
from medflux_backend.Preprocessing.phase_00_detect_type.file_type_enum import FileType

def test_unknown(tmp_path):
    p = tmp_path / "no_such_file.xyz"
    res = detect_file_type(str(p))
    assert res.file_type == FileType.UNKNOWN

def test_pdf(tmp_path):
    p = tmp_path / "sample.pdf"
    p.write_bytes(b"%PDF-1.4\n%...")
    res = detect_file_type(str(p))
    assert res.file_type in {FileType.PDF_TEXT, FileType.PDF_SCANNED}

def test_docx(tmp_path):
    p = tmp_path / "sample.docx"
    p.write_bytes(b"PK\x03\x04")
    res = detect_file_type(str(p))
    assert res.file_type == FileType.DOCX

def test_image(tmp_path):
    p = tmp_path / "sample.jpg"
    p.write_bytes(b"\xFF\xD8\xFF")
    res = detect_file_type(str(p))
    assert res.file_type in {FileType.IMAGE, FileType.UNKNOWN}

def test_txt(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("hello")
    res = detect_file_type(str(p))
    assert res.file_type == FileType.TXT
