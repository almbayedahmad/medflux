@echo off
REM PURPOSE:
REM   Convenience wrapper to bootstrap or activate the MedFlux environment on Windows.
REM   Delegates to the single source of truth: scripts\environment_activate.ps1.
REM
REM OUTCOME:
REM   Calls the PowerShell script with the appropriate flags to create/ensure
REM   the venv, install dependencies, and set session variables.
REM
REM USAGE:
REM   setup_env.bat [--venv <DIR>] [--ensure] [--no-dev] [--dev]
REM     --venv <DIR>   Target virtualenv directory (default handled by PS script)
REM     --ensure       Create venv if missing and install deps
REM     --no-dev       Skip dev dependencies when ensuring
REM     --dev          Install dev dependencies (default)

setlocal ENABLEDELAYEDEXPANSION

set "WRAPPER_DIR=%~dp0"
pushd "%WRAPPER_DIR%" >NUL 2>&1

set "POW_ARGS="

:parse
if "%~1"=="" goto run
if /I "%~1"=="--venv" (
  set "VENV_VAL=%~2"
  set "POW_ARGS=!POW_ARGS! -VenvPath \"%~2\""
  shift & shift
  goto parse
)
if /I "%~1"=="--ensure" (
  set "POW_ARGS=!POW_ARGS! -Ensure"
  shift
  goto parse
)
if /I "%~1"=="--no-dev" (
  set "POW_ARGS=!POW_ARGS! -Dev:$false"
  shift
  goto parse
)
if /I "%~1"=="--dev" (
  set "POW_ARGS=!POW_ARGS! -Dev:$true"
  shift
  goto parse
)
REM Unknown argument: ignore
shift
goto parse

:run
REM Validate --venv path format when provided (must include backslashes)
if defined VENV_VAL (
  echo %VENV_VAL% | findstr /C":" >NUL || goto _skip_validate
  echo %VENV_VAL% | findstr /C:"\" >NUL || (
    echo [env] Invalid --venv path "%VENV_VAL%". Use full Windows path with backslashes, e.g. C:\\venvs\\medflux
    popd >NUL 2>&1
    exit /b 1
  )
)
:_skip_validate
set "PS_SCRIPT=%~dp0scripts\environment_activate.ps1"
if not exist "%PS_SCRIPT%" (
  echo [env] Could not find scripts\environment_activate.ps1
  popd >NUL 2>&1
  exit /b 1
)

echo [env] Executing: powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" !POW_ARGS!
powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" !POW_ARGS!
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo [env] Environment setup failed with code %ERR%.
  popd >NUL 2>&1
  exit /b %ERR%
)

echo [env] Environment is ready. You can now activate the venv if needed.
echo        PowerShell: .\^.venv\Scripts\Activate.ps1  (or your chosen --venv path)
echo        CMD:        call .\^.venv\Scripts\activate.bat

popd >NUL 2>&1
exit /b 0
