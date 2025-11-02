@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Resolve repo root to this script's directory
set "REPO=%~dp0"
pushd "%REPO%" >NUL 2>&1

REM Prefer local virtualenv Python if present
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)

REM Ensure repo is on PYTHONPATH
set "PYTHONPATH=%REPO%"

REM Default: run ALL test layers (unit + integration + smoke)
set "DEFAULT_MARKERS=unit or integration or smoke"

REM Allow passing extra pytest args; if none passed, use default markers
set "ARGS_ORIG=%*"
set "PAUSE_AT_END=0"
if "%ARGS_ORIG%"=="" set "PAUSE_AT_END=1"

REM Check for pytest and httpx; if missing, instruct to install dev requirements
"%PY%" -c "import pytest" >NUL 2>&1
set "NEED_INSTALL=0"
if errorlevel 1 set "NEED_INSTALL=1"
"%PY%" -c "import httpx" >NUL 2>&1
if errorlevel 1 set "NEED_INSTALL=1"
if "%NEED_INSTALL%"=="1" (
  echo [ERROR] Missing test dependencies. Please install dev requirements:
  echo   pip install -r requirements.txt -r requirements-dev.txt
  set "EC=1"
  if "%PAUSE_AT_END%"=="1" pause
  goto :FINISH
)

REM Run tests (default markers if no args)
if "%PAUSE_AT_END%"=="1" (
  echo Running tests with: %PY% -m pytest -q --maxfail=1 --disable-warnings -m "%DEFAULT_MARKERS%"
  "%PY%" -m pytest -q --maxfail=1 --disable-warnings -m "%DEFAULT_MARKERS%"
) else (
  echo Running tests with: %PY% -m pytest -q --maxfail=1 --disable-warnings %ARGS_ORIG%
  "%PY%" -m pytest -q --maxfail=1 --disable-warnings %ARGS_ORIG%
)
set "EC=%ERRORLEVEL%"

REM If launched without args (likely double-click), pause so window doesn't close
if "%PAUSE_AT_END%"=="1" pause

popd >NUL 2>&1
endlocal & exit /b %EC%

:FINISH
popd >NUL 2>&1
endlocal & exit /b %EC%
