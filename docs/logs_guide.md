MedFlux Logs

Paths
- Default root: logs (repo root). Override via MEDFLUX_LOG_ROOT.
- Structured file path when using configure_log_destination(run_id, phase[, flow]):
  - logs/<YYYY-MM-DD>/<RUN_ID>/<PHASE>.jsonl
  - logs/<FLOW>/<YYYY-MM-DD>/<RUN_ID>/<PHASE>.jsonl (if flow provided)

Runtime toggles
- MEDFLUX_LOG_PROFILE: dev (default) or prod; picks policy from core/policy/observability/logging/.
- MEDFLUX_LOG_JSON=1 or MEDFLUX_LOG_FORMAT=json: console logs as JSON via JSONLogFormatter.
- MEDFLUX_LOG_TO_STDERR=1: console handler to stderr (handy in CI).
- MEDFLUX_LOG_FILE=0: disable json_file handler from policy (avoid files in some envs).
- MEDFLUX_LOG_DAILY=1: prefer daily rotation when policy supports it.
- MEDFLUX_TRACE_URL_TEMPLATE: enrich JSON with trace_url for a given trace_id.

Shipping to Loki
- Promtail config is provided under tools/monitoring/promtail; it tails logs/**/*.jsonl.
- Start Loki + Promtail via tools/monitoring/docker-compose.yml profiles.
- Grafana pre-provisioned with a Loki datasource and trace links into Tempo.

Policy references
- core/policy/observability/logging/logging_config.yaml
- core/policy/observability/logging/redaction_rules.yaml
- core/logging/log_record.schema.json (used in CI validator)
