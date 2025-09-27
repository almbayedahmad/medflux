# Medflux Backend Preprocessing

This repository contains the standalone preprocessing pipeline that used to live inside the larger Medflux project. It has been repackaged so it can run from `C:\Users\almba\medflux` with its own virtual environment and tests.

## Environment

1. Activate the virtual environment and move into the project root:
   ```powershell
   Set-Location C:\Users\almba\medflux
   . .\environment_activate.ps1
   ```

   The helper script resolves its own location and sets `PYTHONPATH` accordingly.

2. Install dependencies (only required for a fresh env):
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

## Tests

```powershell
python -m pytest medflux_backend/Preprocessing/test_preprocessing/unit_tests -q
```

## Convenience script

Run the bundled wrapper to process the demo files and optionally open the output folder:
```powershell
scripts\run_samples.ps1 -OpenOutput
```

## Git Remote

```
git remote -v
origin  https://github.com/almbayedahmad/medflux.git (fetch)
origin  https://github.com/almbayedahmad/medflux.git (push)
```

All work now happens from this directory (`C:\Users\almba\medflux`); the old OneDrive copy can be archived.
