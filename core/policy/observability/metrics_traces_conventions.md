# Metrics and Traces Conventions

Naming and tagging conventions for consistent observability.

- Metrics
  - Use snake_case; prefix with domain (e.g., preprocessing_)
  - Counters: processed_items_count; Gauges: memory_usage_mb; Timers: stage_time_ms
  - Tags/labels: phase, pipeline_id, version, status

- Traces
  - Span names: <phase>.<operation> (e.g., readers.ocr)
  - Attributes: run_id, pipeline_id, version, file_path (avoid PII)
