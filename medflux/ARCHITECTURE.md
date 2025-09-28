# Medflux Preprocessing Architecture Overview

This document summarises the structure of the standalone preprocessing
package extracted from the wider Medflux project. It focuses on the key
pipelines and supporting components that enable file type detection,
encoding normalisation, and reader execution.

## High-level flow

The preprocessing CLI entry point is `detect_and_read.py`, which strings
together the detection and reader phases:

1. **File type detection** — uses
   `phase_00_detect_type.file_type_detector.detect_file_type` to inspect
   the binary and PDF structure of each input file in order to classify
   the document and propose downstream reader options.
2. **Encoding detection** — for text-based payloads, the
   `phase_01_encoding.encoding_detector.detect_text_encoding` routine
   checks BOMs and leverages `chardet` (when available) to produce a
   normalised encoding confidence payload.
3. **Reader execution** — the `UnifiedReaders` facade orchestrates the
   format-specific readers (native PDF extraction, OCR, DOCX parsing) and
   consolidates the outputs and metrics.
4. **Metadata emission** — `assemble_doc_meta` merges the detection
   results, reader summary, language/locale hints, table detections, and
   timing metrics into `doc_meta.json` for each processed file.

All artefacts are saved to a per-document output directory, and an
aggregate `detect_and_read_report.json` collects both the raw decisions
and metadata for the batch.

## Pipeline CLI (`pipeline/detect_and_read.py`)

`detect_and_read.main()` glues together the pipeline and exposes CLI
flags for defaults and heuristics. Key responsibilities include:

- Maintaining `sys.path` so the package can be executed as a module.
- Normalising detected language codes (`_split_lang_field`) and
  orchestrating fallback logic when readers fail to emit confident
  hints.
- Building the reader options (`ReaderOptions`) passed to
  `UnifiedReaders`, including table-detection knobs and OCR parameters.
- Tracking per-phase timings (detect, encoding, readers) and injecting
  placeholders for downstream stages such as cleaning or segmentation.
- Collecting reader summaries (counts, QA warnings, table stats) and
  persisting `doc_meta.json` alongside the reader outputs.

The CLI ensures that optional artefacts (`per_page_stats`, `thresholds`)
are passed through when the readers materialise them, keeping the
metadata schema extensible.

## Phase 00 – Type detection (`phase_00_detect_type`)

This package determines the best reader strategy by inspecting the file
extension, MIME type, and, for PDFs, sampling pages with PyMuPDF. Core
components:

- `file_type_detector.detect_pdf()` analyses sampled pages, measuring
  image density, block counts, and text volume to categorise the
  document as native, scanned (OCR), or mixed.
- `detect_file_type()` wraps the heuristics and returns a
  `FileTypeResult` with the inferred `FileType` enum value, confidence,
  and recommended reader parameters (`mode`, `dpi`, `tables_mode`, etc.).
- Constants (e.g. `DEFAULT_SAMPLE_PAGES`, extension allow-lists) codify
  the detection thresholds that downstream readers rely on.

The detector falls back gracefully when PyMuPDF is not available and can
handle DOCX, TXT, and image inputs via extension and MIME checks.

## Phase 01 – Encoding detection (`phase_01_encoding`)

`encoding_detector.detect_text_encoding()` is a lightweight utility that
reads a sample of the input bytes, detects UTF-8 BOMs, and, when
available, consults `chardet` for a best-effort encoding guess. The
result is packaged into a `DetectionInfo` dataclass containing the
encoding name, confidence, BOM presence, and whether the sample decodes
cleanly as UTF-8. These fields flow directly into the `doc_meta`
structure so later pipeline stages can avoid re-detecting encodings.

## Phase 02 – Readers (`phase_02_readers`)

The readers package houses the format-specific logic as well as the
`UnifiedReaders` orchestration layer.

### Format adapters

- `pdf_reader.py` handles native PDF extraction via PyMuPDF, generating
  text blocks, span metadata, table candidates, and timing metrics.
- `ocr_runner.py` and `ocr_table_reader.py` wrap Tesseract/PIL-based OCR
  flows for scanned PDFs and images, including optional table extraction
  from raster data.
- `docx_reader.py` converts DOCX inputs to plain text segments using
  `python-docx`.

All readers funnel their outputs into a normalised record structure so
`UnifiedReaders` can merge them transparently.

### UnifiedReaders responsibilities

`UnifiedReaders` constructs per-page `PageRecord` entries, accumulates
warnings/tool events, and synthesises language/locale hints:

- Tracks page decisions (native vs OCR) and average confidence scores.
- Normalises block-level information (`_build_block_entries`) to capture
  typography and positional metadata for downstream segmentation.
- Collects visual artefacts (`_collect_image_artifacts`) such as stamps,
  signatures, or logos by analysing image bounding boxes.
- Infers lightweight language (`_infer_language_hint`) and locale
  (`_infer_locale_hint`) hints from extracted text patterns, merging them
  across multiple passes (`_merge_hint`).
- Maintains table candidates, raw table structures, and thresholds for
  QA review, ensuring all data is written to the `readers/` subdirectory
  of the output.

The class also logs tool events (`_log_tool_event`) to power the
`processing_log` entries in the emitted metadata, providing observability
into which extractors or fallbacks were used.

## Metadata and QA outputs

`assemble_doc_meta()` (pipeline module) consolidates per-document
summaries into a schema tailored for downstream normalisation/QA
pipelines. It stores:

- File descriptors (type, page counts, block counts, table counts).
- Encoding detection results and language/locale hints, both overall and
  per-page.
- QA flags, warning codes, and segmentation thresholds from readers.
- Visual artefact counts and references to JSONL payloads (`text_blocks`,
  `tables_raw`, `visual_artifacts`).
- Timing breakdowns for the detect/encoding/readers stages, plus slots
  for later phases to fill in cleaning/normalisation/segmentation
  durations.

These artefacts enable later Medflux components to make routing
decisions without re-running the expensive detection and reader phases.

