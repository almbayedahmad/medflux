Docker Compose - Prometheus + Grafana

This setup stands up Prometheus (scraper) and Grafana (dashboards) to monitor MedFlux locally.

Prereqs
- Docker Desktop (Win/Mac) or Docker on Linux
- For app metrics, run MedFlux with:
  - MEDFLUX_MONITORING=1
  - MEDFLUX_PROM_PORT=8000 (or any port)

Files
- docker-compose.yml - launches Prometheus (9090) and Grafana (3000)
- prometheus/prometheus.yml - scrapes host.docker.internal:8000 and :8001 by default
- grafana/provisioning - auto-loads the provided dashboards and Prometheus datasource
 - dashboards/*.json - prebuilt dashboards (validation_health.json, phase_performance.json, validation_codes_by_phase.json, flow_overview.json, api_overview.json, ocr_deep_dive.json)
  - Optional infra: node-exporter (9100) and cAdvisor (8080)
 - alertmanager/alertmanager.yml - Alertmanager config (Slack/Email via env)
 - Dashboards default home: `GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH` points to `dashboards/home.json`

Usage
1) Start stack:
   docker compose up -d

2) Run your app with exporter:
   MEDFLUX_MONITORING=1 MEDFLUX_PROM_PORT=8000 python -m backend.Preprocessing.phase_00_detect_type.pipeline_workflow.detect_type_cli sample.txt --log-json --log-level INFO

3) Open Grafana: http://localhost:3000 (admin/admin)
   Prometheus: http://localhost:9090

4) Import dashboards via API (optional alternative to provisioning):
   - Note: If provisioning is active (default in this setup), the import script will skip provisioned dashboards to avoid duplicates and will import into the 'MedFlux' folder.
   - Set credentials (one of):
     - `set GRAFANA_API_TOKEN=...` or `set GRAFANA_BASIC_AUTH=admin:admin`
   - Run:
     - `python tools/monitoring/load_grafana_dashboards.py`
   - If you previously imported into the General folder and now see duplicates, clean them up:
     - `python tools/monitoring/cleanup_grafana_duplicates.py`

5) Reload Prometheus alert rules (after editing files in tools/monitoring/alerts):
   python tools/monitoring/reload_prometheus_rules.py

New Panels You Can Explore
- Flow Overview: success ratio, validation p95, phase runs
- API Overview: req/s by route, 5xx rate, p95 latency
- OCR Deep Dive: OCR p95 time, avg confidence, docs processed by type
- IO Overview: I/O p95 by op/kind, I/O errors
- Infra Overview: node CPU/mem/disk, container CPU/mem, scrape durations
 - Logs Overview: live logs (Loki) with labels (phase, code, trace_id) and error counts
 - Monitoring Overview: high-level health (active alerts, up targets, validation p95, log rates)

Linux Note
- If host.docker.internal does not resolve, edit prometheus/prometheus.yml to point to your host IP (e.g., 172.17.0.1:8000), then:
  docker compose restart prometheus

Remote Write (Grafana Cloud)
- To forward metrics to Grafana Cloud, configure `remote_write` in `prometheus/prometheus.yml` (already scaffolded).
- Create a local secret file with your access token:
  echo YOUR_GRAFANA_CLOUD_TOKEN_HERE > tools/monitoring/prometheus/remote_write_password.txt
- Ensure your Prometheus instance ID (username) matches in the YAML.
- Restart the stack:
  docker compose up -d
- Verify on Grafana Cloud "Metrics > Prometheus > Remote write status".

Infra Metrics (optional)
- Start exporters (Linux only):
  docker compose -f tools/monitoring/docker-compose.yml --profile linux up -d node-exporter cadvisor
- On Windows/Mac (Docker Desktop), these exporters are disabled by default. For Windows host metrics, you can install `windows_exporter` and add a Prometheus scrape job.

Windows Host Metrics (optional)
- Install exporter: `choco install windows-exporter` (listens on port 9182)
- Add to `tools/monitoring/prometheus/prometheus.yml`:

  job_name: 'windows'
  static_configs:
    - targets: ['host.docker.internal:9182']

- Apply changes: `docker compose -f tools/monitoring/docker-compose.yml restart prometheus`
 - To see process CPU/memory panels, enable the `process` collector in windows_exporter (see the exporter docs for configuring collectors on Windows services).
 - Ensure Windows service is running and accessible:
   - `Get-Service windows_exporter` (PowerShell)
   - Open firewall if needed for 9182 or run on localhost only.
 - The provided Prometheus job 'windows' is already configured in `prometheus.yml` to scrape `host.docker.internal:9182`.

Alerting (Alertmanager)
- Configure Slack/Email via environment variables and start Alertmanager:
  - Slack Webhook: set `SLACK_API_URL`
  - Channels:
    - `SLACK_CHANNEL` (default), `SLACK_CHANNEL_WARN`, `SLACK_CHANNEL_CRIT`
  - Templates use `GRAFANA_URL` and `PROMETHEUS_URL` for links
  - Quick start (Slack):
    1) Copy `tools/monitoring/.env.example` to `tools/monitoring/.env` and set values
    2) `docker compose -f tools/monitoring/docker-compose.yml up -d alertmanager`
    3) `docker compose -f tools/monitoring/docker-compose.yml restart prometheus`
  - Prometheus is configured to send alerts to alertmanager:9093.
  - Email (disabled by default):
    - The repo currently routes email alerts to a blackhole receiver to avoid sending emails unintentionally.
    - To enable email routing:
      - Edit `tools/monitoring/alertmanager/alertmanager.yml` and switch the routes for `severity=warning`/`critical` from `blackhole` back to `email-warning`/`email-critical`.
      - Or, in `tools/monitoring/alertmanager/config.yml`, set `route.receiver: email`.
      - Set in `tools/monitoring/.env`:
        - `SMTP_SMARTHOST`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`
        - `EMAIL_TO` (default recipient), optionally `EMAIL_TO_WARN`, `EMAIL_TO_CRIT`
      - Note: For Gmail, use `smtp.gmail.com:587` and an App Password on your account.
    - Reload: `docker compose -f tools/monitoring/docker-compose.yml restart alertmanager`

Tracing (Tempo)
- A Tempo instance is included for traces.
  - Start: docker compose -f tools/monitoring/docker-compose.yml up -d tempo
  - Grafana datasource "Tempo" is provisioned at http://tempo:3200
- App export config:
  - MEDFLUX_MONITORING=1
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
  - (optional) MEDFLUX_TRACE_URL_TEMPLATE to add trace_url into logs (see core/logging/README.md)

Logs (Loki + Promtail)
- Start Loki and Promtail:
  docker compose -f tools/monitoring/docker-compose.yml up -d loki promtail
- Promtail tails repo logs at `logs/**/*.jsonl` and pushes to Loki.
- Grafana datasource "Loki" is provisioned and derives `trace_id` links to Tempo.

Docker services logging directly to Loki (optional)
- You can have services push container logs directly to Loki via the Loki logging driver.
- Compose already includes a logging block for key services (prometheus, grafana, tempo, dev-exporter, loki, cadvisor).
- Prerequisite: install the Docker Loki logging driver once on the host:
  - Windows PowerShell (Docker Desktop):
    - `docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions`
  - Verify: `docker plugin ls` shows `loki` enabled.
- Restart the stack so logging drivers are applied to new containers.

API Traffic Generator (optional)
- Generate sample API traffic against your running API to populate API panels:
  python tools/monitoring/gen_api_traffic.py --base http://localhost:8000 --duration 60 --rate 5
  - Customize routes: add args after --routes, e.g., --routes /api/v1/health /api/v1/upload /does-not-exist

Test Alerts (Slack/Email routing)
- Send a synthetic alert directly to Alertmanager:
  - Fire warning alert:
    - `python tools/monitoring/send_test_alert.py --severity warning`
  - Fire critical alert:
    - `python tools/monitoring/send_test_alert.py --severity critical`
  - Resolve the alert:
    - `python tools/monitoring/send_test_alert.py --severity warning --resolve`
  - Options:
    - `--url` to point to a remote Alertmanager (default http://localhost:9093)
    - `--label key=value` to add extra labels (repeatable)
    - `--annotation key=value` to add extra annotations (repeatable)

Smoke Monitoring Check
- Quick endpoint verification script (Prometheus, Grafana, Loki, Tempo, Alertmanager):
  - `python tools/monitoring/smoke_check.py`
  - Exits non-zero if any core endpoint is unhealthy; prints details for failures.
