MON_STACK=tools/monitoring/docker-compose.yml

.PHONY: monitoring-up monitoring-down monitoring-restart monitoring-status monitoring-open monitoring-prom-open

monitoring-up:
	docker compose -f $(MON_STACK) up -d
	@echo "Grafana: http://localhost:3000 | Prometheus: http://localhost:9090"

monitoring-down:
	docker compose -f $(MON_STACK) down

monitoring-restart:
	docker compose -f $(MON_STACK) down
	docker compose -f $(MON_STACK) up -d
	@echo "Grafana: http://localhost:3000 | Prometheus: http://localhost:9090"

monitoring-status:
	docker compose -f $(MON_STACK) ps

monitoring-open:
	python -c "import webbrowser; webbrowser.open('http://localhost:3000')"

monitoring-prom-open:
	python -c "import webbrowser; webbrowser.open('http://localhost:9090')"

.PHONY: test test-fast test-golden

# Run default fast pack with coverage, silencing OTEL exporter
test:
	OTEL_TRACES_EXPORTER=none \
	pytest -m "unit or contract or component" -q --cov=core --cov=backend --cov-report=xml

# Run default fast pack (no coverage), silencing OTEL exporter
test-fast:
	OTEL_TRACES_EXPORTER=none \
	pytest -q

# Run only golden tests, silencing OTEL exporter
test-golden:
	OTEL_TRACES_EXPORTER=none \
	pytest -m golden -q

# -----------------------------------------------------------------------------
# Umbrella CLI shortcuts (optional developer convenience)
# -----------------------------------------------------------------------------

.PHONY: phase-list detect encoding readers chain

LOG_FLAGS?=--log-level INFO --log-json

phase-list:
	python -m core.cli.medflux phase-list

detect:
	python -m core.cli.medflux $(LOG_FLAGS) phase-detect --inputs $(INPUTS) $(if $(OUTPUT_ROOT),--output-root $(OUTPUT_ROOT),)

encoding:
	python -m core.cli.medflux $(LOG_FLAGS) phase-encoding --inputs $(INPUTS) $(if $(NORMALIZE),--normalize,) $(if $(OUTPUT_ROOT),--output-root $(OUTPUT_ROOT),)

readers:
	python -m core.cli.medflux $(LOG_FLAGS) phase-readers --inputs $(INPUTS) $(if $(OUTPUT_ROOT),--output-root $(OUTPUT_ROOT),)

chain:
	python -m core.cli.medflux $(LOG_FLAGS) chain-run --inputs $(INPUTS) $(if $(OUTPUT_ROOT),--output-root $(OUTPUT_ROOT),) $(if $(INCLUDE_DOCS),--include-docs,)

# -----------------------------------------------------------------------------
# Samples smoke runner (first 3 phases)
# -----------------------------------------------------------------------------

.PHONY: smoke-samples smoke-open

SMOKE_OUT?=.artifacts/smoke
SMOKE_PHASES?=detect encoding readers
LIMIT?=2

smoke-samples:
	python tools/smoke/run_samples_smoke.py --phases $(SMOKE_PHASES) --out-root $(SMOKE_OUT) --limit $(LIMIT)
	@echo "Smoke summary written to $(SMOKE_OUT)/smoke_summary.json"

smoke-open:
	python - <<'PY'
	import os, platform, subprocess, pathlib
	p = pathlib.Path(os.environ.get('SMOKE_OUT','$(SMOKE_OUT)')).expanduser().resolve()
	try:
	    if platform.system() == 'Windows':
	        os.startfile(str(p))  # type: ignore[attr-defined]
	    elif platform.system() == 'Darwin':
	        subprocess.run(['open', str(p)], check=False)
	    else:
	        subprocess.run(['xdg-open', str(p)], check=False)
	except Exception:
	    print(str(p))
	PY

# Intentionally no env bootstrap targets here; use scripts/environment_activate.ps1

.PHONY: clean-repo clean-repo-dry

clean-repo:
	python tools/maintenance/clean_repo.py --yes --verbose

clean-repo-dry:
	python tools/maintenance/clean_repo.py --dry-run

.PHONY: monitoring-load-dashboards monitoring-reload-alerts

monitoring-load-dashboards:
	GRAFANA_URL?=http://localhost:3000 \
	python tools/monitoring/load_grafana_dashboards.py

monitoring-reload-alerts:
	PROMETHEUS_URL?=http://localhost:9090 \
	python tools/monitoring/reload_prometheus_rules.py
