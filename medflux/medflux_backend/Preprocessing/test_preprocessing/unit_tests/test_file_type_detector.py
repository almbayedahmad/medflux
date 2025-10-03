from medflux_backend.Preprocessing.phase_00_detect_type.internal_helpers.detect_type_detection_helper import process_detect_type_file
from medflux_backend.Preprocessing.phase_00_detect_type.schemas.detect_type_types import FileType

def test_unknown(tmp_path):
    p = tmp_path / "no_such_file.xyz"
    res = process_detect_type_file(str(p))
    assert res.file_type == FileType.UNKNOWN

def test_pdf(tmp_path):
    p = tmp_path / "sample.pdf"
    p.write_bytes(b"%PDF-1.4\n%...")
    res = process_detect_type_file(str(p))
    assert res.file_type in {FileType.PDF_TEXT, FileType.PDF_SCANNED}

def test_docx(tmp_path):
    p = tmp_path / "sample.docx"
    p.write_bytes(b"PK\x03\x04")
    res = process_detect_type_file(str(p))
    assert res.file_type == FileType.DOCX

def test_image(tmp_path):
    p = tmp_path / "sample.jpg"
    p.write_bytes(b"\xFF\xD8\xFF")
    res = process_detect_type_file(str(p))
    assert res.file_type in {FileType.IMAGE, FileType.UNKNOWN}

def test_txt(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("hello")
    res = process_detect_type_file(str(p))
    assert res.file_type == FileType.TXT
