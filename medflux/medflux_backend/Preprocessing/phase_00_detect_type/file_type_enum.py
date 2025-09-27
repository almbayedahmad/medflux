from enum import Enum

class FileType(str, Enum):
    PDF_TEXT = "pdf_text"
    PDF_SCANNED = "pdf_scanned"
    PDF_MIXED = "pdf_mixed"
    DOCX = "docx"
    IMAGE = "image"
    TXT = "txt"
    UNKNOWN = "unknown"

