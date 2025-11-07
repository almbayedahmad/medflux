# MedFlux

Core services and tooling for MedFlux: preprocessing stages, API, policies (logging, validation, versioning), CI/CD, and local observability.

Highlights
- Versioning: single source of truth at `core/versioning/VERSION`; releases via GitHub Actions.
- Quality gates: tests + coverage (project ≥ 80%, patch ≥ 80%), schema compatibility guard in CI.
- Structured logging: policy-driven JSON logs, redaction, daily rotation (prod), queue handler in prod.
- Observability: Prometheus + Grafana + Loki + Tempo via `tools/monitoring`.
- Contracts: JSON Schemas for stages and artifacts with validators and dry‑run demotions.

Quick links
- Repo structure: docs/STRUCTURE.md
- Architecture overview: docs/architecture_overview.md
- Validation playbook: docs/validation_playbook.md
- Branch protection: docs/BRANCH_PROTECTION.md

Note on alerts
- Email notifications are currently disabled by routing to a blackhole receiver in Alertmanager. See `tools/monitoring/alertmanager/alertmanager.yml` to re‑enable by switching warning/critical routes back to email.

## Environment

1. (First run) create a virtual environment in place:
   `powershell
   python -m venv .venv
   `
2. Activate the tooling and switch into the project:
   `powershell
   . .\\scripts\\environment_activate.ps1
   `
   The helper picks a .venv in this folder by default. Pass -VenvPath if you want to reuse another environment.
3. Install Python dependencies:
   `powershell
   pip install -r requirements.txt
   `

## Running a stage on samples

`powershell
# Detect type stage (example)
python -m backend.Preprocessing.main_pre_phases.phase_00_detect_type.pipeline_workflow.detect_type_cli samples\Sample.txt --log-json --log-level INFO
`
> Ensure `PYTHONPATH='.'` if running module entry points directly.

All output artefacts (reports, per-file summaries, raw readers output) end up inside the folder passed to --outdir.

The detect phase now surfaces a lightweight table detector. Per-file summaries include a `table_stats` list and `table_pages` flag,
and you can tune the heuristics via `--table-detect-min-area` and `--table-detect-max-cells` when running the CLI.

Every processed document also emits a `doc_meta.json` alongside the readers output. The metadata captures file type, page count, encoding and language hints, OCR presence, plus per-stage timings so downstream merge/cleaning steps can reuse the signals without reprocessing the original files. Companion files `text_blocks.jsonl`, `zones.jsonl`, and `structured_logs.jsonl` expose reading-order blocks, page zoning metadata, and structured reader events for downstream processing, while `doc_meta.json` adds page-level language and locale hints that later phases can refine.

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
- `text_blocks`, `zones`, `structured_logs`, and `artifacts` are mirrored inline in `doc_meta.json` while retaining their JSONL export paths for downstream consumers.

### QA thresholds & actions

- `qa.low_conf_pages` marks pages where OCR confidence dropped below 70. Re-run OCR (prefer `deu+eng` with deskew/denoise at 300–400 dpi) and keep the page on manual review if it stays low.
- `qa.low_text_pages` flags pages with fewer than 10 OCR words but high confidence (covers, photos, stamps). Treat them as intentional non-text pages, not OCR failures.
- `qa.tables_fail` indicates every table extraction attempt failed. Enable fallbacks (Camelot → Tabula → OCR table crops) and mark the document for manual review.
- `qa.reasons` aggregates these triggers so downstream tooling can explain why `needs_review` flipped.


Use these hints, stats, and logs to drive later merge/normalisation phases (for example, switching decimal handling when `locale_hints.overall` is `de`, or rerunning OCR when `qa.needs_review` is true).


### Metadata doc meta module

The consolidated metadata schema lives under `medflux_backend/Preprocessing/output_structure/readers_outputs/`.
The `doc_meta.py` entry point assembles `doc_meta.json` by loading reader summaries, timers, text blocks, tables, QA flags, and log events.
- Doc metadata now records OCR runtime details (`ocr_engine`, `ocr_engine_version`, `ocr_langs`), preprocessing steps (`preprocess_applied`), a stable `content_hash`, detected `bbox_origin` / `pdf_locked` / `has_text_layer`, and the refined per-page timings (including `table_detect_light`).
- Per-page stats are normalised (`source` as `text|ocr|mixed`, language fallbacks, rotation, `page_size`, multi-column flag, `ocr_conf`).
- Text blocks carry structured presentation hints (`font_size`, `paragraph_style`, `list_level`) alongside existing OCR confidence and language tags.
Adjustments to the JSON contract should happen in `components.py` (shared helpers), `per_page_stats.py` (per-page details), and `text_blocks.py` (block-level details), with coverage in `test_doc_meta.py`.

## Running tests & coverage

`powershell
pytest -q --maxfail=1 --disable-warnings --cov=. --cov-report=term
`
- CI requires project coverage ≥ 80% and patch coverage ≥ 80% (Codecov).
- See `.coveragerc` for measured scope (focus on `core` and `backend/api`).

## API quick start
`powershell
uvicorn backend.api.main:app --reload --port 8000
`
- Health: `GET /api/v1/health`
- Version: `GET /api/v1/version`

## CI & Releases
- CI: `.github/workflows/ci.yaml` runs lint, tests, schema checks, packaging, smoke, integration, and security.
- Schema compatibility guard: blocks breaking schema changes unless MAJOR version increases.
- Releases: bump `core/versioning/VERSION`, tag `vX.Y.Z`, or run the manual Release workflow.

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

## Session Notes (2025-10-03)
- Unified the readers CLI under `run_readers.py`; legacy `detect_and_read` now wraps the new entry point.
- Readers emit structured logs (`readers/structured_logs.jsonl`) and zoning metadata (`readers/zones.jsonl`); `tables_raw` was retired.
- `doc_meta.json` now aligns with the `readers.v1` schema (`schema_version`, `run_id`, `pipeline_id`, top-level `zones`, `logs_structured`).
- Added lightweight per-page geometry for DOCX (A4 EMU estimates) and images, feeding per-page stats and zones.
- Introduced `utils/logger.py` for JSONL event logging; future reader tooling should use it instead of ad-hoc prints.
- Added `tests/smoke_readers.sh` to exercise the CLI across PDF, DOCX, and image samples.

### Recommended Checks
- `PYTHONPATH='.' pytest medflux_backend/Preprocessing/test_preprocessing/unit_tests/test_doc_meta.py -q`
- Run `tests/smoke_readers.sh` from a POSIX shell (Git Bash/WSL) to validate end-to-end processing.


## Latest Progress (2025-09-30)
- Started feature branch `feat/readers-hardening` and created shared scaffolding directories (`configs/`, `utils/`, `schemas/`, `readers_outputs/`).
- Relocated the doc metadata core (`components`, `doc_meta`, `per_page_stats`, `text_blocks`, `types`) into the top-level `readers_outputs` package to provide a single import surface.
- Added initial utility modules (`utils/lang_utils.py`, `utils/num_utils.py`, `utils/geom_utils.py`) as the home for shared language/number/bbox helpers.
- Centralised reader thresholds/features in `configs/readers.yaml` with the shared `CFG` loader and removed ad-hoc constants in the pipeline.
- Simplified reader outputs to emit table candidates only, disabled heavy extraction by default, and trimmed doc metadata to the lean readers schema.
- Normalised all bounding boxes to the bottom-left origin, pruned block-level word fallbacks, and introduced per-page QA flags based on configured thresholds.
- Added `schemas/readers_output_schema.py` to document the required readers payload contract for downstream consumers.

## Next Steps
1. Wire the new readers schema into downstream validation and document sample payloads alongside the schema stub.
2. Provide a configuration toggle + documentation for re-enabling heavy table extraction when required by hospitals.
3. Expand test coverage for per-page QA flags and coordinate conversions (e.g., golden doc_meta fixtures).


1. Replace duplicated helper functions in the readers metadata modules with imports from `utils/` and finish centralising the logic.
2. Introduce the YAML-backed readers config (`configs/readers.yaml`) and loader, wiring thresholds/feature flags via `CFG[...]`.
3. Re-run `python -m pytest medflux_backend/Preprocessing/test_preprocessing/unit_tests -q` and smoke the CLI to confirm the refactor.
4. Capture updated screenshots/log outputs once the new config and utils are active.
