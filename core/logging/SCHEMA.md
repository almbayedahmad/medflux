# Logging Schema (MedFlux)

Minimum fields (recommended):
- ts (ms), time (ISO), level, logger, message
- run_id, flow, phase, stage
- hostname, pid
- code (for warnings/errors), file_id, input_path, output_path
- app_version (optional; include via context)

All logs should be JSON when formatters.json is active, and carry the context via `log_context` or a context filter.
