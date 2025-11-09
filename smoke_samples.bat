@echo off
REM PURPOSE:
REM   Run MedFlux smoke checks for the first three preprocessing phases
REM   (detect, encoding, readers) against repository samples.
REM
REM OUTCOME:
REM   Writes artifacts and a JSON summary under .artifacts\smoke and opens
REM   the folder on request. Uses policy-compliant logging; no stdout prints.
REM
REM INPUTS (optional flags):
REM   --out <DIR>         Output root (default: .artifacts\smoke)
REM   --limit <N>         Max files per sample group (default: 2)
REM   --phases <LIST>     Space-separated phases (default: detect encoding readers)
REM   --export-xlsx       Enable XLSX export in readers (optional)
REM   --open              Open the output folder after run
REM   --no-json-log       Do not enable JSON logging for this run
REM   --pause             Pause at end (default when no args)
REM   --no-pause          Do not pause

setlocal ENABLEDELAYEDEXPANSION

REM Resolve repo root as the directory of this script
set "_ROOT=%~dp0"
pushd "%_ROOT%" >NUL 2>&1

REM Defaults
set "OUT=.artifacts\smoke"
set "LIMIT=2"
set "PHASES=detect encoding readers"
set "DO_EXPORT_XLSX="
set "DO_OPEN="
set "DO_JSON_LOG=1"
set "DO_PAUSE="

REM Parse simple flags
REM If no args were provided, default to pausing at the end for visibility
if "%~1"=="" (
  set "DO_PAUSE=1"
  goto run
)

:parse
if "%~1"=="" goto run
if /I "%~1"=="--out"          ( set "OUT=%~2" & shift & shift & goto parse )
if /I "%~1"=="--limit"        ( set "LIMIT=%~2" & shift & shift & goto parse )
if /I "%~1"=="--phases"       ( set "PHASES=%~2" & shift & shift & goto parse )
if /I "%~1"=="--export-xlsx"  ( set "DO_EXPORT_XLSX=1" & shift & goto parse )
if /I "%~1"=="--open"         ( set "DO_OPEN=1" & shift & goto parse )
if /I "%~1"=="--no-json-log"  ( set "DO_JSON_LOG=" & shift & goto parse )
if /I "%~1"=="--pause"        ( set "DO_PAUSE=1" & shift & goto parse )
if /I "%~1"=="--no-pause"     ( set "DO_PAUSE=" & shift & goto parse )
REM Unknown flag -> ignore
shift
goto parse

:run
REM Configure logging profile for local smoke
set "MEDFLUX_LOG_PROFILE=dev"
if defined DO_JSON_LOG set "MEDFLUX_LOG_JSON=1"
set "MEDFLUX_LOG_LEVEL=INFO"

REM Ensure output dir exists
if not exist "%OUT%" mkdir "%OUT%" >NUL 2>&1

REM Ensure local package is importable if not installed
set "PYTHONPATH=%CD%;%PYTHONPATH%"

set "EXTRA="
if defined DO_EXPORT_XLSX set "EXTRA=--export-xlsx"

echo Running: python "%~dp0tools\smoke\run_samples_smoke.py" --out-root "%OUT%" --limit %LIMIT% --phases %PHASES% %EXTRA%
python "%~dp0tools\smoke\run_samples_smoke.py" --out-root "%OUT%" --limit %LIMIT% --phases %PHASES% %EXTRA%
if errorlevel 1 (
  echo Smoke run failed. See logs above.
  popd >NUL 2>&1
  exit /b 1
)

echo.
echo Smoke summary:
if exist "%OUT%\smoke_summary.json" (
  type "%OUT%\smoke_summary.json"
) else (
  echo (no summary found at "%OUT%\smoke_summary.json")
)

if defined DO_OPEN (
  echo Opening "%OUT%" ...
  start "" "%OUT%"
)

if defined DO_PAUSE pause

popd >NUL 2>&1
exit /b 0
