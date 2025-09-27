param(
    [string]$ProjectRoot = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [string]$VenvPath
)

$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not $PSBoundParameters.ContainsKey("VenvPath")) {
    $candidate = Join-Path $ProjectRoot ".venv"
    if (Test-Path $candidate) {
        $VenvPath = $candidate
    } else {
        $VenvPath = "C:\\venvs\\medflux"
    }
}

if (-not (Test-Path $VenvPath)) {
    throw "Virtual environment path '$VenvPath' was not found. Pass -VenvPath to point to an existing environment."
}

$activateScript = Join-Path $VenvPath "Scripts"
$activateScript = Join-Path $activateScript "Activate.ps1"
if (-not (Test-Path $activateScript)) {
    $activateScript = Join-Path $VenvPath "bin"
    $activateScript = Join-Path $activateScript "Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        throw "Activate script not found inside '$VenvPath'."
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "Activating virtual environment from $activateScript" -ForegroundColor Cyan
    Write-Host "Tip: dot-source this script to keep it active in your current shell: . .\\environment_activate.ps1" -ForegroundColor Yellow
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
