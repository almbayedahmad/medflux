from pathlib import Path
from typing import List, Dict, Optional
import io, statistics, time

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None

# ----- helpers -----
def _avg_conf_from_tsv(tsv_text: str) -> Optional[float]:
    if not tsv_text:
        return None
    lines = tsv_text.splitlines()
    if not lines:
        return None
    header = lines[0].strip().split('\t')
    try:
        conf_idx = header.index('conf')
    except ValueError:
        conf_idx = -1
    vals = []
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if conf_idx >= 0 and len(parts) > conf_idx:
            raw = parts[conf_idx].strip()
            try:
                c = float(raw)
            except Exception:
                continue
            if c >= 0:
                vals.append(c)
    if not vals:
        return None
    return round(statistics.mean(vals), 2)

def _clamp(x: int, lo: int = 200, hi: int = 450) -> int:
    return max(lo, min(hi, x))

def _median_font_size(page) -> Optional[float]:
    """Estimate median font size if PDF has extractable text."""
    try:
        d = page.get_text("dict")  # requires PyMuPDF
    except Exception:
        return None
    sizes = []
    for b in d.get("blocks", []):
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                sz = s.get("size")
                if isinstance(sz, (int, float)) and sz > 0:
                    sizes.append(float(sz))
    if not sizes:
        return None
    sizes.sort()
    mid = sizes[len(sizes)//2]
    return float(mid)

def _recommend_dpi_for_page(page, default: int = 300) -> int:
    """
    Simple heuristic:
      - If page has text: use median font size
          <7.5pt -> 400 DPI
          <9.5pt -> 350 DPI
          else  -> 300 DPI
      - If no text (likely scanned) -> 350 DPI
    """
    try:
        med_sz = _median_font_size(page)
    except Exception:
        med_sz = None
    if med_sz is None:
        dpi = 350
    elif med_sz < 7.5:
        dpi = 400
    elif med_sz < 9.5:
        dpi = 350
    else:
        dpi = 300
    return _clamp(dpi)

# ----- main -----
def ocr_pages(
    pdf_path: str,
    page_numbers_1based: List[int],
    lang: str = "eng",
    dpi: int = 300,
    psm: int = 3,
    oem: int = 1,
    pre: Optional[str] = None,
    save_tsv: bool = False,
    outdir: Optional[Path] = None,
    dpi_mode: str = "fixed"  # "fixed" | "auto"
) -> List[Dict]:
    """
    Returns: list of pages with fields:
      page_no, mode, text, text_len, avg_conf, tokens, dpi, oem, pre, time_ms
    """
    if fitz is None or pytesseract is None or Image is None:
        raise RuntimeError("OCR prerequisites missing: PyMuPDF/PIL/pytesseract")
    doc = fitz.open(pdf_path)
    results: List[Dict] = []
    try:
        for pno in page_numbers_1based:
            page = doc.load_page(pno-1)
            dpi_used = _recommend_dpi_for_page(page, default=dpi) if dpi_mode == "auto" else _clamp(int(dpi))

            # render page
            t0 = time.time()
            zoom = dpi_used / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            # preprocessing (optional)
            if pre:
                try:
                    from .ocr_optimizer import apply_pipeline
                    steps = [x for x in pre.split(",") if x.strip()]
                    img = apply_pipeline(img, steps)
                except Exception:
                    # do not fail OCR if pre-processing fails
                    pass

            config = f"--psm {psm} --oem {oem}"
            text = pytesseract.image_to_string(img, lang=lang, config=config) or ""
            tsv  = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.STRING)
            elapsed = int((time.time() - t0) * 1000)

            avg_conf = _avg_conf_from_tsv(tsv)
            results.append({
                "page_no": pno,
                "mode": "ocr",
                "text": text,
                "text_len": len(text),
                "avg_conf": avg_conf,
                "tokens": None,
                "dpi": dpi_used,
                "oem": oem,
                "pre": pre,
                "time_ms": elapsed
            })

            if save_tsv and outdir:
                outdir.mkdir(parents=True, exist_ok=True)
                (outdir / f"ocr_page_{pno:03d}.tsv").write_text(tsv, encoding="utf-8")
    finally:
        doc.close()
    return results


