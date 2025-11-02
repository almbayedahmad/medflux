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

.PHONY: monitoring-load-dashboards monitoring-reload-alerts

monitoring-load-dashboards:
	GRAFANA_URL?=http://localhost:3000 \
	python tools/monitoring/load_grafana_dashboards.py

monitoring-reload-alerts:
	PROMETHEUS_URL?=http://localhost:9090 \
	python tools/monitoring/reload_prometheus_rules.py
