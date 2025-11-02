@echo off
echo Starting monitoring stack...
docker compose -f tools/monitoring/docker-compose.yml up -d
echo Grafana: http://localhost:3000 ^| Prometheus: http://localhost:9090
echo To start API (requires uvicorn installed):
echo   set MEDFLUX_MONITORING=1
echo   set MEDFLUX_PROM_PORT=8000
echo   set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
echo   uvicorn backend.api.main:app --port 8000
