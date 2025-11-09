param(
    [string]$ProjectRoot,
    [string]$VenvPath,
    [switch]$Ensure = $false,
    [switch]$Dev = $true
)

# Resolve project root to repository root (parent of scripts directory) if not provided
if (-not $PSBoundParameters.ContainsKey('ProjectRoot') -or [string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $ProjectRoot = Split-Path -Parent $scriptDir
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not $PSBoundParameters.ContainsKey("VenvPath")) {
    $candidate = Join-Path $ProjectRoot ".venv"
    if (Test-Path $candidate) {
        $VenvPath = $candidate
    } else {
        $VenvPath = "C:\\venvs\\medflux"
    }
}

# Normalize quoting and drive syntax in VenvPath if present
if ($null -ne $VenvPath) {
    $VenvPath = [string]$VenvPath
    $VenvPath = $VenvPath.Trim()
    if ($VenvPath.StartsWith('"') -or $VenvPath.StartsWith("'")) {
        $VenvPath = $VenvPath.Substring(1)
    }
    if ($VenvPath.EndsWith('"') -or $VenvPath.EndsWith("'")) {
        $VenvPath = $VenvPath.Substring(0, $VenvPath.Length - 1)
    }
    # Normalize paths like C:venvsmedflux -> C:\venvsmedflux (add missing backslash after drive)
    if ($VenvPath -match '^[A-Za-z]:(?!\\)') {
        $VenvPath = $VenvPath.Insert(2, '\')
    }
}

if (-not (Test-Path $VenvPath)) {
    if ($Ensure) {
        Write-Host "[env] Creating virtual environment at $VenvPath" -ForegroundColor Cyan
        python -m venv $VenvPath
        if (-not (Test-Path $VenvPath)) {
            throw "Failed to create venv at '$VenvPath'. Ensure Python is installed and the path is valid."
        }
    } else {
        throw "Virtual environment path '$VenvPath' was not found. Pass -VenvPath to point to an existing environment or use -Ensure to create and set it up."
    }
}

$activateScript = Join-Path -Path $VenvPath -ChildPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    $activateScript = Join-Path -Path $VenvPath -ChildPath "bin/Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        throw "Activate script not found inside '$VenvPath'. Expected 'Scripts\Activate.ps1' or 'bin/Activate.ps1'."
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Write-Host ("Activating virtual environment from {0}" -f $activateScript) -ForegroundColor Cyan
    Write-Host "Tip: dot-source this script to keep it active in your current shell: . .\\scripts\\environment_activate.ps1" -ForegroundColor Yellow
}

& $activateScript

Set-Location $ProjectRoot

if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $ProjectRoot
} elseif (-not $env:PYTHONPATH.Split([IO.Path]::PathSeparator) -contains $ProjectRoot) {
    $env:PYTHONPATH = $ProjectRoot + [IO.Path]::PathSeparator + $env:PYTHONPATH
}

try {
    & python --version
} catch {
    Write-Warning "Python executable not found after activation."
}

# Optional bootstrap inside the selected venv
if ($Ensure) {
    # Prefer Windows Scripts\pip.exe; fallback to POSIX bin/pip
    $pip = Join-Path -Path $VenvPath -ChildPath "Scripts\pip.exe"
    if (-not (Test-Path $pip)) {
        $pip = Join-Path -Path $VenvPath -ChildPath "bin/pip"
    }
    try {
        & $pip install --upgrade pip
        if (Test-Path (Join-Path $ProjectRoot 'requirements.txt')) {
            Write-Host "[env] Installing requirements.txt" -ForegroundColor Cyan
            & $pip install -r (Join-Path $ProjectRoot 'requirements.txt')
        }
        if ($Dev -and (Test-Path (Join-Path $ProjectRoot 'requirements-dev.txt'))) {
            Write-Host "[env] Installing requirements-dev.txt" -ForegroundColor Cyan
            & $pip install -r (Join-Path $ProjectRoot 'requirements-dev.txt')
        }
        Write-Host "[env] Installing project (editable) from $ProjectRoot" -ForegroundColor Cyan
        & $pip install -e "$ProjectRoot"
    } catch {
        Write-Warning "Failed to install dependencies: $_"
    }
}

# Session logging defaults for local dev
$env:MEDFLUX_LOG_PROFILE = 'dev'
$env:MEDFLUX_LOG_LEVEL = 'INFO'
