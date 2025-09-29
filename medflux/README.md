# Medflux Backend Preprocessing

Standalone OCR-driven preprocessing pipeline (file type detection, encoding normalisation, readers) extracted from the larger Medflux project.

## Environment

1. (First run) create a virtual environment in place:
   `powershell
   python -m venv .venv
   `
2. Activate the tooling and switch into the project:
   `powershell
   . .\environment_activate.ps1
   `
   The helper picks a .venv in this folder by default. Pass -VenvPath if you want to reuse another environment.
3. Install Python dependencies:
   `powershell
   pip install -r requirements.txt
   `

## Running the pipeline on samples

`powershell
python -m medflux_backend.Preprocessing.pipeline.detect_and_read 
    samples\Sample_pdfmixed.pdf 
    samples\Sample_pdftext.pdf 
    samples\sample_pdfscanned.pdf 
    samples\demo_vertrag.docx 
    samples\Sample.txt 
    --outdir output\run_20250927_1528
`
> **Note**: When invoking the CLI directly with `python -m medflux_backend...` make sure the repository root is on `PYTHONPATH` (e.g. PowerShell: `$env:PYTHONPATH='.'`).

All output artefacts (reports, per-file summaries, raw readers output) end up inside the folder passed to --outdir.

The detect phase now surfaces a lightweight table detector. Per-file summaries include a `table_stats` list and `table_pages` flag,
and you can tune the heuristics via `--table-detect-min-area` and `--table-detect-max-cells` when running the CLI.

Every processed document also emits a `doc_meta.json` alongside the readers output. The metadata captures file type, page count, encoding and language hints, OCR presence, plus per-stage timings so downstream merge/cleaning steps can reuse the signals without reprocessing the original files. Companion files `text_blocks.jsonl` and `tables_raw.jsonl` expose reading-order blocks and raw table structures (bbox, extraction source, cell grid) for downstream merge logic, while `doc_meta.json` adds page-level language and locale hints that later phases can refine.

### doc_meta.json language payload

```

{

  "detected_languages": {

    "overall": ["de", "en"],

    "by_page": [

      {"page": 1, "languages": ["de"]},

      {"page": 2, "languages": ["de", "en"]}

    ]

  },

  "locale_hints": {

    "overall": "de",

    "by_page": [

      {"page": 1, "locale": "de"},

      {"page": 2, "locale": "mixed"}

    ]

  },

  "qa": {

    "needs_review": false,

    "pages": [],

    "warnings": []

  },

  "processing_log": [

    {"step": "pymupdf_open", "status": "ok"},

    {"step": "ocr_runner", "status": "ok", "details": {"pages": [2, 8], "lang": "deu+eng"}},

    {"step": "table_extract", "status": "fallback", "page": 2, "details": {"tool": "camelot"}}

  ],

  "visual_artifacts_count": 1,

  "visual_artifacts_path": "readers/visual_artifacts.jsonl"

}

```

- `detected_languages.by_page` originates from reader heuristics (keywords, OCR tokens, block hints). Pages that only surface `unknown` fall back to the detector/CLI language defaults.
- `detected_languages.overall` contains deduplicated language codes returned by the per-page hints or, when no confident hints exist, the fallback defaults.
- `locale_hints.by_page` exposes lightweight number/date style detection per page (`de`, `en`, `mixed`, or `unknown`).
- `locale_hints.overall` collapses all page hints to a single best guess, preferring confident page hits over `unknown` and resorting to `mixed` when conflicting evidence exists.
- `qa.needs_review` surfaces the enrichment flags (warnings + per-page low confidence) so you can short-circuit manual validation when false.
- `processing_log` lists the document-level tool chain (major readers, fallbacks, table extractors) so downstream stages understand how content was produced.
- `visual_artifacts_path` (plus `visual_artifacts_count`) enumerates detected stamps/signatures/logos with page-level bounding boxes for UI overlays.
- `per_page_stats` now carries `lang`, `locale`, `tables_found`, per-page timings, and the derived `flags` (for example `low_conf_page`, `low_text_page`) alongside the legacy counters.
- `timings_ms` breaks readers work into fine-grained slices (text extraction, OCR, table detection/extraction, language hint detection) in addition to the total runtime.
- `text_blocks`, `tables_raw`, and `artifacts` are mirrored inline in `doc_meta.json` while retaining their JSONL export paths for downstream consumers.

### QA thresholds & actions

- `qa.low_conf_pages` marks pages where OCR confidence dropped below 70. Re-run OCR (prefer `deu+eng` with deskew/denoise at 300–400 dpi) and keep the page on manual review if it stays low.
- `qa.low_text_pages` flags pages with fewer than 10 OCR words but high confidence (covers, photos, stamps). Treat them as intentional non-text pages, not OCR failures.
- `qa.tables_fail` indicates every table extraction attempt failed. Enable fallbacks (Camelot → Tabula → OCR table crops) and mark the document for manual review.
- `qa.reasons` aggregates these triggers so downstream tooling can explain why `needs_review` flipped.


Use these hints, stats, and logs to drive later merge/normalisation phases (for example, switching decimal handling when `locale_hints.overall` is `de`, or rerunning OCR when `qa.needs_review` is true).


### Metadata doc meta module

The consolidated metadata schema lives under `medflux_backend/Preprocessing/output_structure/readers_outputs/`.
The `doc_meta.py` entry point assembles `doc_meta.json` by loading reader summaries, timers, text blocks, tables, QA flags, and log events.
- Doc metadata now records OCR runtime details (ocr_engine, ocr_engine_version, ocr_langs), preprocessing steps (preprocess_applied), a stable content_hash, detected box_origin, pdf_locked status, and the derived has_text_layer flag alongside per-stage timings (including 	able_detect_light).
Adjustments to the JSON contract should happen in `components.py` (shared helpers), `per_page_stats.py` (per-page details), and `text_blocks.py` (block-level details), with coverage in `test_doc_meta.py`.

## Running tests

`powershell
python -m pytest medflux_backend/Preprocessing/test_preprocessing/unit_tests -q
`

## Repository layout

- nvironment_activate.ps1 ? Activation helper that locates the virtual environment and exports PYTHONPATH.
- medflux_backend/ ? Namespaced preprocessing package (detectors, readers, CLI).
- samples/ ? Demo documents for manual smoke tests.
- .benchmarks, .pytest_cache, output/ ? Runtime artefacts ignored by git.

## Git remote

`
git remote -v
origin  https://github.com/almbayedahmad/medflux.git (fetch)
origin  https://github.com/almbayedahmad/medflux.git (push)
`

Use the standard Git workflow (git status, git commit, git push) from the repository root.
