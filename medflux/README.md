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

  ]

}

```

- `detected_languages.by_page` originates from reader heuristics (keywords, OCR tokens, block hints). Pages that only surface `unknown` fall back to the detector/CLI language defaults.
- `detected_languages.overall` contains deduplicated language codes returned by the per-page hints or, when no confident hints exist, the fallback defaults.
- `locale_hints.by_page` exposes lightweight number/date style detection per page (`de`, `en`, `mixed`, or `unknown`).
- `locale_hints.overall` collapses all page hints to a single best guess, preferring confident page hits over `unknown` and resorting to `mixed` when conflicting evidence exists.
- `qa.needs_review` surfaces the enrichment flags (warnings + per-page low confidence) so you can short-circuit manual validation when false.
- `processing_log` lists the document-level tool chain (major readers, fallbacks, table extractors) so downstream stages understand how content was produced.

Use these hints and logs to drive later merge/normalisation phases (for example, switching decimal handling when `locale_hints.overall` is `de`).


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
