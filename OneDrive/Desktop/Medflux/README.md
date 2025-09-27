# Medflux Backend Preprocessing

This repository contains the standalone preprocessing pipeline that used to live inside the larger Medflux project. It has been repackaged so it can run from `C:\Users\almba\medflux` with its own virtual environment and tests.

## Environment

1. Activate the virtual environment and move into the project root:
   ```powershell
   Set-Location C:\Users\almba\medflux
   . .\environment_activate.ps1
   ```

   The helper script resolves its own location and sets `PYTHONPATH` accordingly, so it no longer depends on the old OneDrive folder.

2. Install Python dependencies (only needed for a fresh environment):
   ```powershell
   pip install -r requirements.txt
   ```

## Running the pipeline on samples

```powershell
python medflux_backend/Preprocessing/pipeline/detect_and_read.py `
    samples\Sample_pdfmixed.pdf `
    samples\Sample_pdftext.pdf `
    samples\sample_pdfscanned.pdf `
    samples\demo_vertrag.docx `
    samples\Sample.txt `
    --outdir output\run_$(Get-Date -Format yyyyMMdd_HHmm)
```

All output artefacts (JSON reports, extracted text, per-page summaries) will land inside the folder specified by `--outdir`.

## Running tests

```powershell
python -m pytest medflux_backend/Preprocessing/test_preprocessing/unit_tests -q
```

## Repository layout

- `environment_activate.ps1` – activation helper that targets the `C:\venvs\medflux_backend` virtualenv and switches to this repo’s root.
- `medflux_backend/` – namespaced preprocessing package (detectors, readers, CLI).
- `samples/` – demo documents for manual runs.
- `scripts/` – local utility scripts (e.g. `run_samples.ps1`).
- `.benchmarks`, `.pytest_cache` – pytest artefacts (ignored by git).

## Git remote

This repository is already configured with the remote `origin`:

```
git remote -v
origin  https://github.com/almbayedahmad/medflux.git (fetch)
origin  https://github.com/almbayedahmad/medflux.git (push)
```

Use the standard Git workflow from this directory (`git status`, `git commit`, `git push`).
