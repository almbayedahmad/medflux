$ErrorActionPreference = 'Continue'

Write-Host '--- MedFlux Monitoring Debug Check ---'

Write-Host '1) Docker version'
try { docker --version } catch { Write-Warning $_ }

Write-Host '2) Docker compose version'
try { docker compose version } catch { Write-Warning $_ }

Write-Host '3) Docker ps'
try { docker ps --format 'table {{.Names}}	{{.Status}}' } catch { Write-Warning $_ }

Write-Host '4) Prometheus reachable?'
try { (Invoke-WebRequest -UseBasicParsing http://localhost:9090  -TimeoutSec 3).StatusCode } catch { Write-Warning $_ }

Write-Host '5) Grafana reachable?'
try { (Invoke-WebRequest -UseBasicParsing http://localhost:3000 -TimeoutSec 3).StatusCode } catch { Write-Warning $_ }

Write-Host '6) Metrics exporter on 8000/8001 (optional)'
foreach ($p in @(8000,8001)) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing ("http://localhost:{0}/metrics" -f $p) -TimeoutSec 2
    Write-Host " - :$p -> $($resp.StatusCode)"
  } catch {
    Write-Warning " - :$p -> not responding"
  }
}

Write-Host 'Done.'
