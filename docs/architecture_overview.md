Architecture Overview (Plan Layers → Repo)

Layer A – Versioning
- Version file: core/versioning/VERSION
- Policy: core/policy/versioning/*
- CI checks: .github/workflows/ci.yaml (policy-version job), tools/versioning/verify_version.py

Layer B – Testing
- Pytest config: pytest.ini (markers, discovery)
- Tests tree: tests/{unit,component,contract,integration,golden,smoke,e2e}
- CI: .github/workflows/ci.yaml (tests matrix), .github/workflows/tests.yml (fast pack)

Layer C – Validation (Contracts)
- Schemas: core/validation/contracts/** (JSON Schema, Draft 2020-12)
- Tools: tools/validation/validate_schemas.py, tools/schema/verify_schema_version.py
- Phase validation: tools/validation/validate_phase.py

Layer D – Logging (Structured)
- Runtime: core/logging/{__init__.py,json_formatter.py,redaction.py,log_record.schema.json}
- Policy: core/policy/observability/logging/{logging_config.yaml,redaction_rules.yaml}
- CI log validation: tools/logs/validate_records.py used in ci.yaml (smoke job)
- Docs: docs/logs_guide.md

Layer E – Monitoring / Observability
- Stack: tools/monitoring/{docker-compose.yml,prometheus, grafana, loki, tempo, alertmanager}
- Metrics: core/monitoring/metrics.py; API endpoint in backend/api/main.py
- Dashboards: tools/monitoring/dashboards/*.json
- Alerts: tools/monitoring/alerts/*.yaml

Layer F – CI/CD Integration
- Workflows: .github/workflows/{ci.yaml,tests.yml,release.yml,release-drafter.yml}
- Python toolchain action: .github/actions/python-setup
- Packaging parity: ci.yaml package-parity job

Layer G – Infrastructure & Documentation
- Compose: tools/monitoring/docker-compose.yml
- Repo structure: docs/STRUCTURE.md
- This overview: docs/architecture_overview.md
