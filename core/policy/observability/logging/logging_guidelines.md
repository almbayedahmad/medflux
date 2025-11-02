# Logging Guidelines

This document summarizes logging conventions for MedFlux.

Required fields (JSON formatter)
- time (ISO) and ts (ms)
- level, logger, message
- run_id, phase (in pipeline contexts)
- hostname, pid (context filter injects defaults)
- code on WARNING/ERROR/CRITICAL records

Codes and severities
- Codes are namespaced by stage and type (e.g., RD-W001, EN-E001, DT-W001)
- Use WARNING for recoverable issues; ERROR for failing operations; CRITICAL for fatal errors
- See `core/policy/observability/logging/event_codes.yaml`

Context
- Use `set_ctx(run_id=..., phase=...)` at the start of a run; `ContextFilter` injects fields automatically
- Wrap key blocks with `log_context` for local overrides (e.g., stage="tables")

Formatting and destinations
- Console format defaults to text in dev, JSON in prod (overrides: MEDFLUX_LOG_FORMAT, MEDFLUX_LOG_JSON)
- JSONL files are rotated and stored at `logs/YYYY-MM-DD/<run_id>/<phase>.jsonl`
- Use MEDFLUX_LOG_TO_STDERR=1 for CLI logs on stderr so stdout remains machine-readable

Protection
- Redaction is on by default; sensitive keys and patterns are scrubbed
- Long values are truncated; non-serializable extras are represented with repr()

Examples
```
log.info("CLI start")
log_code("RD-W001", level="WARNING", page=3)
emit_json_event(stage="readers", event="tables_detected", count=3)
```
