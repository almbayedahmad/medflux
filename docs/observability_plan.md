# MedFlux Observability Layer (Production-Grade)

This document summarizes the observability setup implemented in this repo and how to run it locally on Windows.

## Goals
- Unified, production-grade observability: Metrics, Traces, and Logs.
- End-to-end tracing via OpenTelemetry with environment-based config.
- Log correlation: trace_id/span_id injected into logs.
- Ready-to-use Grafana dashboards and Prometheus alert rules.

## Components
- core.monitoring: Prometheus + OpenTelemetry metrics and tracing.
- core.logging: JSON logs with context injection and redaction hooks.
- backend.api: FastAPI with request middleware for logging, metrics, and tracing.
- tools/monitoring: Docker Compose stack (Prometheus, Grafana, Tempo, Loki, Alertmanager) + dashboards and alerts.

## Environment Variables
| Variable | Purpose |
|---------|---------|
| MEDFLUX_MONITORING | Enable monitoring init (1/true/yes) |
| MEDFLUX_PROM_PORT | Start Prometheus exporter HTTP on this port |
| MEDFLUX_OTLP_ENDPOINT | OTLP endpoint for traces (e.g., http://localhost:4318) |
| MEDFLUX_TRACE_SAMPLING | Tracing sampler: always/never or ratio 0..1 |
| MEDFLUX_ENV | Deployment environment (e.g., dev/staging/prod) |
| MEDFLUX_SERVICE_NAME | OTEL service.name override |
| MEDFLUX_VERSION | OTEL service.version override |
| OTEL_TRACES_EXPORTER | Set to `none` to disable exporting in tests |
| OTEL_METRICS_EXPORTER | Set to `none` to disable OTEL metrics exporter |

## API Instrumentation
- Request middleware logs and records metrics for every request.
- A tracing span `http.request` is created with attributes: route, method, path, client.ip, user_agent, request_id, and status code.
- Response headers include `x-request-id` and `traceparent` (when present).

## Dashboards and Alerts
- Grafana dashboards provisioned under tools/monitoring/dashboards: API Overview, Validation Health, Phase Performance, and more.
- Prometheus alert rules in tools/monitoring/alerts: High API error rate, high p95 latency, validation fail rate, SLO burn alerts.

## Running Locally (Windows)
1) Start the monitoring stack:
   - PowerShell: `docker compose -f tools/monitoring/docker-compose.yml up -d`
2) Run the API with exporters:
   - PowerShell:
     - `$env:MEDFLUX_MONITORING='1'`
     - `$env:MEDFLUX_PROM_PORT='8000'`
     - `$env:OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4318'`
     - `uvicorn backend.api.main:app --port 8000`
3) Open Grafana: http://localhost:3000 (admin/admin), Prometheus: http://localhost:9090

## Tips
- In tests/CI, exporters are silenced by default to avoid network calls.
- To correlate logs and traces in Grafana, enable Tempo and Loki in the stack (provided by the Compose file).
