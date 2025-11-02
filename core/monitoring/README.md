Monitoring overview

Backends
- Dev: Prometheus exporter (env MEDFLUX_PROM_PORT)
- Prod: OpenTelemetry OTLP (uses standard OTEL_* envs)

Enable
- Set MEDFLUX_MONITORING=1 to initialize metrics/tracing (no-op otherwise)
- For Prometheus (dev): MEDFLUX_PROM_PORT=8000
- For OTLP (prod): set OTEL_EXPORTER_OTLP_ENDPOINT and optional headers

Metrics (names)
- Prometheus: medflux_validation_ok_total, medflux_validation_failed_total{code}, medflux_validation_duration_ms (histogram), medflux_phase_runs_total{status}
- OTEL: medflux.validation.ok, medflux.validation.failed, medflux.validation.duration.ms, medflux.phase.runs
- Flows: medflux_flow_runs_total, medflux_flow_duration_ms (histogram) | OTEL: medflux.flow.runs, medflux.flow.duration.ms
 - Docs: medflux_docs_processed_total{phase,type}, medflux_doc_bytes (hist) | OTEL: medflux.docs.processed, medflux.doc.bytes
 - OCR: medflux_ocr_time_ms (hist), medflux_ocr_confidence (hist) | OTEL: medflux.ocr.time.ms, medflux.ocr.confidence
 - API: medflux_api_requests_total{route,method,status}, medflux_api_duration_ms (hist) | OTEL: medflux.api.requests, medflux.api.duration.ms
 - Steps: medflux_phase_step_duration_ms{phase,step} (hist) | OTEL: medflux.phase.step.duration.ms
 - I/O: medflux_io_duration_ms{op,kind} (hist), medflux_io_errors_total{op,kind} | OTEL: medflux.io.duration.ms, medflux.io.errors
 - Validator: medflux_validator_requests_total{phase,kind}, medflux_validator_compiles_total{phase,kind} | OTEL: medflux.validator.requests/compiles

Tracing
- Spans: validation.input, validation.output, phase.run
- Logs include trace_id/span_id via logging context when tracing active

Dashboards & Alerts
- Grafana dashboards: tools/monitoring/dashboards/*.json
- Prometheus alert rules: tools/monitoring/alerts/validation_alerts.yaml

Dev quickstart
- python tools/monitoring/self_check.py
- curl http://localhost:8001/metrics

Facades
- `from core.monitoring import get_monitor` → exposes `inc("flow_runs_total", labels={"flow": name})` and `timer("flow_duration_ms", labels={"flow": name})`.
- `from core.monitoring import validation_span` → context manager that opens a tracing span and records validation metrics automatically.
 - Additional helpers: `record_doc_processed`, `observe_ocr_time_ms`, `observe_ocr_confidence`, `observe_api_request`, `observe_phase_step_duration`, `observe_io_duration`, `record_io_error`, `record_validator_request`, `record_validator_compile`.

API
- The FastAPI app exposes `/metrics` (Prometheus format) when `prometheus-client` is installed.

Testing
- Install dev deps: `pip install -r requirements-dev.txt`
- Run tests: `pytest -q tests/test_monitoring_prometheus.py -q`
  - Tests pick a free port automatically and verify:
    - medflux_validation_* counters/histogram are emitted
    - medflux_phase_runs_total increments by status
  - If OpenTelemetry is installed, `tests/test_monitoring_tracing.py` additionally checks that
    `start_phase_span` injects `trace_id` into the logging context.

CI
- A GitHub Actions workflow at `.github/workflows/ci.yml` runs these tests on push/PR
  with Python 3.12 and dev dependencies.
