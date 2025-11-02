# Logging Policies and Configuration

This folder contains the logging policies for MedFlux.

- Configs
  - `logging_config.yaml` — base config (console + JSONL rotation)
  - `logging_config.dev.yaml` — dev profile (text console, DEBUG level)
  - `logging_config.prod.yaml` — prod profile (JSON console, queue, filters)

- Rules and Guides
  - `event_codes.yaml` — taxonomy for warning/error codes
  - `redaction_rules.yaml` — sensitive keys/patterns redaction rules
  - `logging_fields.md` — context and event fields
  - `logging_policy.md` — principles and retention
  - `logging_guidelines.md` — how to log (examples and conventions)

Set `MEDFLUX_LOG_PROFILE=dev|prod` to select a profile. Overrides are available via env:
- `MEDFLUX_LOG_LEVEL` (DEBUG|INFO|WARNING|ERROR|CRITICAL)
- `MEDFLUX_LOG_FORMAT=text|json` or `MEDFLUX_LOG_JSON=1`
- `MEDFLUX_LOG_FILE=0` to disable file handler (console-only)
- `MEDFLUX_LOG_DAILY=1` to use daily rotation when available
 - `MEDFLUX_LOG_ROOT` to set the logs root directory (default: `<repo>/logs` in dev)

Filters tuning (when enabled in policy):
- `MEDFLUX_LOG_SAMPLING_N` (default 10) — keep 1 of N records
- `MEDFLUX_LOG_RATE_WINDOW_S` (default 10), `MEDFLUX_LOG_RATE_MAX_EVENTS` (default 50)
- `MEDFLUX_LOG_DUP_TTL` seconds (default 2) — suppress duplicate messages
