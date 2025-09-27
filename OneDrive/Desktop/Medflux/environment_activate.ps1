param(
    [string]$VenvPath = "C:\venvs\medflux",
    [string]$ProjectRoot = "C:\Users\almba\OneDrive\Desktop\Medflux"
)

if (-not (Test-Path $VenvPath)) {
    throw "Virtual environment path '$VenvPath' was not found. Run the setup first."
}

$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Activate script '$activateScript' is missing."
}

if ($PSCommandPath) {
    Write-Host "Activating virtual environment from $activateScript" -ForegroundColor Cyan
    Write-Host "Tip: dot-source this script to keep it active in your current shell: . .\environment_activate.ps1" -ForegroundColor Yellow
}

& $activateScript

if (Test-Path $ProjectRoot) {
    Set-Location $ProjectRoot
}

try {
    & python --version
} catch {
    Write-Warning "Python executable not found after activation."
}

