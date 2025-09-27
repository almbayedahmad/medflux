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
