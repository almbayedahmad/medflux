from __future__ import annotations
"""Lightweight readers shim with native, OCR, and document handlers."""
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover - optional deps at runtime
    fitz = None
    Image = None
    pytesseract = None

from .docx_reader import read_docx_to_text
from .pdf_reader import read_pdf_text

DOCX_EXTS = {".docx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
TEXT_EXTS = {".txt", ".log", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".ini", ".cfg", ".conf"}


@dataclass
class ReaderOptions:
    mode: str = "mixed"
    lang: str = "deu"
    dpi_mode: str = "auto"
    oem: int = 3
    dpi: int = 300
    psm: int = 6
    workers: int = 4
    use_pre: bool = False
    export_xlsx: bool = False
    verbose: bool = False
    tables_mode: str = "light"
    save_table_crops: bool = False
    tables_min_words: int = 12
    blocks_threshold: int = 3
    native_ocr_overlay: bool = False
    overlay_area_thr: float = 0.35
    overlay_min_images: int = 1
    overlay_if_any_image: bool = False


@dataclass
class Summary:
    files: List[str]
    page_count: int
    avg_conf: float
    warnings: List[str]
    timings_ms: Dict[str, float]
    page_decisions: List[str]


@dataclass
class PageRecord:
    file: str
    page: int
    source: str
    text: str
    conf: float = 0.0


def _safe_avg_conf(conf_list) -> float:
    values: List[float] = []
    for value in conf_list or []:
        try:
            float_value = float(value)
        except Exception:
            continue
        if float_value > 0:
            values.append(float_value)
    return sum(values) / len(values) if values else 0.0


class UnifiedReaders:
    def __init__(self, outdir: Path, opts: ReaderOptions):
        self.outdir = Path(outdir)
        self.opts = opts
        self._records: List[PageRecord] = []
        self._warnings: List[str] = []
        self._page_decisions: List[str] = []
        self._tables: List[Dict[str, str]] = []
        self._t0 = time.time()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _ocr_page_image(self, image) -> tuple[str, float]:
        if pytesseract is None:
            return "", 0.0
        try:
            cfg = f"-l {getattr(self.opts, 'lang', 'eng')} --oem {getattr(self.opts, 'oem', 3)} --psm {getattr(self.opts, 'psm', 6)}"
            data = pytesseract.image_to_data(image, output_type="dict", config=cfg)
            words = data.get("text", []) or []
            confs = data.get("conf", []) or []
            text = " ".join(word for word in words if word and word.strip() and word != "-1")
            return text, _safe_avg_conf(confs)
        except Exception as exc:  # pragma: no cover - depends on runtime OCR availability
            self._warnings.append(f"fallback_ocr_error: {exc}")
            return "", 0.0

    def _ocr_image_file(self, path: Path) -> None:
        if Image is None:
            self._warnings.append("pil_missing")
            return
        try:
            image = Image.open(path).convert("RGB")
            text, conf = self._ocr_page_image(image)
            self._records.append(PageRecord(file=str(path), page=1, source="ocr", text=text, conf=conf))
            self._page_decisions.append("ocr")
        except Exception as exc:
            self._warnings.append(f"read_image_error: {exc}")

    def _pdf_native(self, path: Path) -> None:
        if fitz is not None:
            try:
                doc = fitz.open(path)
            except Exception as exc:  # pragma: no cover - external lib error
                self._warnings.append(f"pdf_open_error: {exc}")
                return
            for index, page in enumerate(doc):
                text = page.get_text("text") or ""
                conf = 100.0 if text.strip() else 0.0
                self._records.append(PageRecord(file=str(path), page=index + 1, source="native", text=text, conf=conf))
                self._page_decisions.append("native")
            return
        try:
            text = read_pdf_text(str(path))
            if text:
                self._records.append(PageRecord(file=str(path), page=1, source="native", text=text, conf=100.0))
                self._page_decisions.append("native")
        except Exception as exc:
            self._warnings.append(f"pdf_native_error: {exc}")

    def _pdf_ocr(self, path: Path) -> None:
        dpi = getattr(self.opts, "dpi", 300)
        try:
            doc = fitz.open(path)
        except Exception as exc:  # pragma: no cover
            self._warnings.append(f"pdf_open_error: {exc}")
            return
        for index, page in enumerate(doc):
            try:
                pixmap = page.get_pixmap(dpi=dpi)
                mode = "RGBA" if getattr(pixmap, "alpha", 0) else "RGB"
                image = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
                text, conf = self._ocr_page_image(image)
                self._records.append(PageRecord(file=str(path), page=index + 1, source="ocr", text=text, conf=conf))
                self._page_decisions.append("ocr")
            except Exception as exc:
                self._warnings.append(f"pdf_page_error: p{index + 1}: {exc}")

    def _pdf_mixed(self, path: Path) -> None:
        blocks_thr = getattr(self.opts, "blocks_threshold", 3)
        try:
            doc = fitz.open(path)
        except Exception as exc:
            self._warnings.append(f"pdf_open_error: {exc}")
            return
        for index, page in enumerate(doc):
            text = page.get_text("text") or ""
            if len(page.get_text("blocks") or []) >= blocks_thr and text.strip():
                self._records.append(PageRecord(file=str(path), page=index + 1, source="native", text=text, conf=100.0))
                self._page_decisions.append("native")
                continue
            try:
                pixmap = page.get_pixmap(dpi=getattr(self.opts, "dpi", 300))
                mode = "RGBA" if getattr(pixmap, "alpha", 0) else "RGB"
                image = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
                text, conf = self._ocr_page_image(image)
            except Exception as exc:
                self._warnings.append(f"pdf_page_error: p{index + 1}: {exc}")
                text, conf = "", 0.0
            self._records.append(PageRecord(file=str(path), page=index + 1, source="ocr", text=text, conf=conf))
            self._page_decisions.append("ocr")

    def _docx_native(self, path: Path) -> None:
        try:
            text = read_docx_to_text(str(path))
            self._records.append(PageRecord(file=str(path), page=1, source="native", text=text, conf=100.0 if text else 0.0))
            self._page_decisions.append("native")
        except Exception as exc:
            self._warnings.append(f"docx_error: {exc}")

    def _text_native(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            self._records.append(PageRecord(file=str(path), page=1, source="native", text=text, conf=100.0 if text else 0.0))
            self._page_decisions.append("native")
        except Exception as exc:
            self._warnings.append(f"text_error: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, inputs) -> Dict[str, object]:
        files: List[str] = []
        mode = (self.opts.mode or "mixed").lower()
        for item in inputs:
            path = Path(item)
            files.append(str(path))
            ext = path.suffix.lower()
            if ext == ".pdf":
                if mode == "native":
                    self._pdf_native(path)
                elif mode == "ocr":
                    self._pdf_ocr(path)
                else:
                    self._pdf_mixed(path)
            elif ext in DOCX_EXTS:
                self._docx_native(path)
            elif ext in TEXT_EXTS:
                self._text_native(path)
            elif ext in IMAGE_EXTS:
                self._ocr_image_file(path)
            else:
                self._ocr_image_file(path)

        self._write_outputs(files)
        avg_conf = _safe_avg_conf([record.conf for record in self._records])
        total_ms = (time.time() - self._t0) * 1000.0
        summary = Summary(
            files=files,
            page_count=len(self._page_decisions),
            avg_conf=avg_conf,
            warnings=self._warnings,
            timings_ms={"total_ms": total_ms},
            page_decisions=self._page_decisions,
        )
        return {
            "summary": asdict(summary),
            "pages_count": len(self._page_decisions),
            "tables_cells": len(self._tables),
            "outdir": str(self.outdir),
        }

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------
    def _write_outputs(self, inputs) -> None:
        output_dir = self.outdir
        output_dir.mkdir(parents=True, exist_ok=True)

        jsonl_path = output_dir / "unified_text.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as handle:
            for record in self._records:
                handle.write(
                    json.dumps(
                        {
                            "file": record.file,
                            "page": record.page,
                            "source": record.source,
                            "text": record.text,
                            "conf": record.conf,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        txt_path = output_dir / "unified_text.txt"
        with open(txt_path, "w", encoding="utf-8") as handle:
            for record in self._records:
                handle.write(f"# file={record.file} page={record.page} conf={record.conf:.2f}\n")
                handle.write(record.text.strip() + "\n\n")

        avg_conf = _safe_avg_conf([record.conf for record in self._records])
        total_ms = (time.time() - self._t0) * 1000.0
        summary = {
            "files": list({record.file for record in self._records}) or [str(p) for p in inputs],
            "page_count": len(self._page_decisions),
            "avg_conf": avg_conf,
            "warnings": self._warnings,
            "timings_ms": {"total_ms": total_ms},
            "page_decisions": self._page_decisions,
        }
        summary_path = output_dir / "readers_summary.json"
        summary_path.write_text(json.dumps({"summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            _enrich_summary_on_disk(output_dir, self.opts)
        except Exception as exc:
            self._warnings.append(f"enrich_error: {exc}")


# === auto-added: enrich readers_summary with per_page_stats / thresholds / flags ===
def _enrich_summary_on_disk(outdir: Path, opts: ReaderOptions):
    """Enrich readers_summary.json with per-page statistics and review flags."""
    import csv
    import json
    from collections import defaultdict

    summary_path = Path(outdir) / "readers_summary.json"
    if not summary_path.exists():
        return

    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return

    summary = payload.get("summary", {}) or {}
    pages = int(summary.get("page_count", 0) or 0)
    decisions = summary.get("page_decisions", []) or []
    warnings = summary.get("warnings", []) or []

    thresholds = dict(payload.get("thresholds", {}) or {})
    thresholds.setdefault("any_min_conf", 70.0)
    thresholds.setdefault("ocr_min_conf", 80.0)
    thresholds.setdefault("low_conf", 70.0)
    thresholds.setdefault("boost_conf", 80.0)
    thresholds.setdefault("overlay_area_thr", float(getattr(opts, "overlay_area_thr", 0.35)))
    thresholds.setdefault("overlay_min_images", int(getattr(opts, "overlay_min_images", 1)))
    payload["thresholds"] = thresholds

    words_per_page = defaultdict(int)
    try:
        jsonl_path = Path(outdir) / "unified_text.jsonl"
        if jsonl_path.exists():
            for line in jsonl_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                page_no = int(obj.get("page", 0) or 0)
                words = str(obj.get("text", "")).split()
                words_per_page[page_no] += len(words)
    except Exception:
        pass

    per_page = []
    for page in range(1, pages + 1):
        decision = (decisions[page - 1] if page - 1 < len(decisions) else "native") or "native"
        source = "ocr" if "ocr" in decision.lower() else "native"
        per_page.append(
            {
                "page": page,
                "source": source,
                "conf": 0.0,
                "ocr_words": int(words_per_page.get(page, 0)),
                "has_table": False,
                "table_cells": 0,
                "decision": decision,
                "time_ms": 0,
            }
        )

    payload["per_page_stats"] = per_page

    flagged = []
    any_thr = float(thresholds.get("any_min_conf", 70.0))
    ocr_thr = float(thresholds.get("ocr_min_conf", 80.0))
    for record in per_page:
        if record["conf"] < any_thr or ("ocr" in record["source"] and record["conf"] < ocr_thr):
            flagged.append(record["page"])

    payload["flags"] = {"manual_review": bool(warnings) or bool(flagged), "pages": flagged}
    summary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    csv_path = Path(outdir) / "per_page_stats.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["page", "source", "conf", "ocr_words", "has_table", "table_cells", "decision", "time_ms"],
            )
            writer.writeheader()
            writer.writerows(per_page)
    except Exception:
        pass
# === end auto-added enrichment ===
