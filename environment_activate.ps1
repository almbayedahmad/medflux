param(
    [string]$VenvPath = "C:\venvs\medflux_backend",
    [string]$ProjectRoot = $PSScriptRoot
)

Write-Host "ProjectRoot param: $ProjectRoot"

if (-not (Test-Path $VenvPath)) {
    throw "Virtual environment path '$VenvPath' was not found. Run the setup first."
}

$activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    throw "Activate script '$activateScript' is missing."
}

& $activateScript

if (Test-Path $ProjectRoot) {
    $resolvedProject = (Resolve-Path $ProjectRoot).ProviderPath
    Write-Host "Resolved project: $resolvedProject"
    $env:PYTHONPATH = $resolvedProject
    Set-Location $resolvedProject
}

try {
    & python --version
} catch {
    Write-Warning "Python executable not found after activation."
}
