# Start local monitoring stack (Prometheus, Grafana, Tempo, Loki, Alertmanager)
param(
  [int]$PromPort = 8000,
  [string]$OtlpEndpoint = "http://localhost:4318",
  [switch]$StartApi
)

Write-Host "Starting monitoring stack..."
docker compose -f tools/monitoring/docker-compose.yml up -d

Write-Host "Grafana: http://localhost:3000 | Prometheus: http://localhost:9090"
Write-Host "To view Tempo and Loki datasources, open Grafana > Explore"

if ($StartApi) {
  $env:MEDFLUX_MONITORING='1'
  $env:MEDFLUX_PROM_PORT="$PromPort"
  $env:OTEL_EXPORTER_OTLP_ENDPOINT=$OtlpEndpoint
  Write-Host "Starting API on port 8000 (requires uvicorn installed)"
  try {
    uvicorn backend.api.main:app --port 8000
  } catch {
    Write-Warning "uvicorn not found. Install with: pip install uvicorn"
  }
} else {
  Write-Host "API not started. To run: `$env:MEDFLUX_MONITORING='1'; `$env:MEDFLUX_PROM_PORT='$PromPort'; `$env:OTEL_EXPORTER_OTLP_ENDPOINT='$OtlpEndpoint'; uvicorn backend.api.main:app --port 8000"
}
