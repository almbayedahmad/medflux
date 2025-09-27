param(
    [switch]$OpenOutput
)

$repoRoot = (Resolve-Path "$PSScriptRoot\..\").ProviderPath
$timestamp = Get-Date -Format yyyyMMdd_HHmm
$outDir = Join-Path $repoRoot "output\samples_$timestamp"

Push-Location $repoRoot
try {
    . .\environment_activate.ps1
    python medflux_backend/Preprocessing/pipeline/detect_and_read.py `
        samples\Sample_pdfmixed.pdf `
        samples\Sample_pdftext.pdf `
        samples\sample_pdfscanned.pdf `
        samples\demo_vertrag.docx `
        samples\Sample.txt `
        --outdir $outDir

    if ($OpenOutput) {
        Invoke-Item $outDir
    }
}
finally {
    Pop-Location
}
