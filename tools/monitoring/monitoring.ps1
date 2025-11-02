# PowerShell helpers for MedFlux monitoring stack

param(
  [ValidateSet('up','down','restart','status','open','prom-open','open-all')]
  [string]$Command = 'status'
)

$compose = Join-Path $PSScriptRoot 'docker-compose.yml'
if (-not (Test-Path $compose)) {
  Write-Error "Compose file not found: $compose"
  exit 1
}

function Up {
  try {
    & docker compose -f $compose up -d
    if ($LASTEXITCODE -ne 0) {
      throw "docker compose returned exit code $LASTEXITCODE"
    }
    Write-Host 'Grafana: http://localhost:3000 | Prometheus: http://localhost:9090'
  } catch {
    Write-Error "Failed to start stack: $($_.Exception.Message)"
    Write-Host "Try running manually: docker compose -f `"$compose`" up -d"
    exit 1
  }
}

function Down {
  & docker compose -f $compose down
}

function Restart {
  & docker compose -f $compose down
  & docker compose -f $compose up -d
  Write-Host 'Grafana: http://localhost:3000 | Prometheus: http://localhost:9090'
}

function Status {
  docker compose -f $compose ps
}

function Open-Grafana {
  Start-Process 'http://localhost:3000'
}

function Open-Prometheus {
  Start-Process 'http://localhost:9090'
}

function Open-All {
  try { Start-Process 'http://localhost:3000' } catch {}
  try { Start-Process 'http://localhost:9090' } catch {}
  try { Start-Process 'http://localhost:9093' } catch {}
}

switch ($Command) {
  'up' { Up }
  'down' { Down }
  'restart' { Restart }
  'status' { Status }
  'open' { Open-Grafana }
  'prom-open' { Open-Prometheus }
  'open-all' { Open-All }
}
