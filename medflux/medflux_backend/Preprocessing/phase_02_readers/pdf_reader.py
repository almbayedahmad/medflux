from typing import Optional
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

def read_pdf_text(path: str, max_pages: Optional[int] = None) -> str:
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed")
    doc = fitz.open(path)
    pages = range(len(doc)) if max_pages is None else range(min(max_pages, len(doc)))
    parts = []
    for i in pages:
        page = doc.load_page(i)
        txt = page.get_text("text") or ""
        if txt.strip():
            parts.append(txt.rstrip())
    return "\n\n".join(parts).strip()


