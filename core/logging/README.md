Simple logging layer with policy-driven configuration and structured context.

Key pieces
- configure_logging() - applies `core/policy/observability/logging_config.yaml`.
- get_logger(name) - returns a configured logger.
- with_context(logger, **fields) - attaches standard fields to a logger.
- log_context(logger, **fields) - context manager for temporary fields.
- Optional JSON logs - set `MEDFLUX_LOG_JSON=1` to switch console to JSON.
- Default file root (dev) is `<repo>/logs`; override with `MEDFLUX_LOG_ROOT` (e.g., for prod paths).
- MEDFLUX_LOG_TO_STDERR=1 routes console output to stderr (useful in CI).
- MEDFLUX_LOG_FILE=0 disables file handler(s) defined in policy.
- MEDFLUX_LOG_DAILY=1 switches `json_file` to `json_file_daily` if available (prod).
- Optional trace URL enrichment: set `MEDFLUX_TRACE_URL_TEMPLATE` to include a `trace_url` field when `trace_id` is present in log context.
  - Example (Tempo direct): `http://localhost:3200/trace/{trace_id}`
  - Example (Grafana Explore): `http://localhost:3000/explore?left=%7B%22datasource%22:%22Tempo%22,%22queries%22:%5B%7B%22query%22:%22{trace_id}%22%7D%5D%7D`

Quick usage
```python
from core.logging import configure_logging, get_logger, with_context

configure_logging()  # reads policy if present
log = with_context(get_logger("demo"), pipeline_id="pre", run_id="test-1")
log.info("hello world")
```

JSON logs
- Policy includes a `json` formatter via `core.logging.json_formatter.JSONLogFormatter`.
- Toggle at runtime with env `MEDFLUX_LOG_JSON=1` (console handler switches to JSON if configured).

Best practices
- Include `version`, `pipeline_id`, `run_id`, and `flow` fields (CoreLoader adds `version`, `pipeline_id`, `run_id`).
- Never log secrets/PII (see `core/policy/observability/logging_policy.md`).

Prod profile specifics
- `MEDFLUX_LOG_PROFILE=prod` enables JSON console, duplicate/sampling/ratelimit filters, and attaches a QueueHandler by default.
- Daily rotation is available via `json_file_daily` in prod; enable with `MEDFLUX_LOG_DAILY=1`.

Anchoring file handlers
- File handlers defined with `filename: logs/current.jsonl` are anchored to `MEDFLUX_LOG_ROOT` if not absolute; directories are created if missing.

Routing file destinations
- `configure_log_destination(run_id, phase, flow=None, root=None)` rewires file handlers at runtime to `<root>/<flow?>/<YYYY-MM-DD>/<run_id>/<phase>.jsonl`.
