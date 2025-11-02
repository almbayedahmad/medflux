Quick Start

Setup
- Python 3.11+ recommended (project is tested on 3.10–3.12)
- Create venv and install dependencies:

  PowerShell
  - python -m venv .venv
  - . .\scripts\environment_activate.ps1
  - pip install -r requirements.txt

Run a sample
- Detect type:
  - set PYTHONPATH=.
  - python -m backend.Preprocessing.main_pre_phases.phase_00_detect_type.pipeline_workflow.detect_type_cli samples\Sample.txt --log-json --log-level INFO

Logs
- JSON logs write under logs/<YYYY-MM-DD>/<RUN>/<PHASE>.jsonl once you call configure_log_destination.
- Toggle JSON console with MEDFLUX_LOG_JSON=1.
- See logs/README.md for more.

Monitoring (Prometheus + Grafana + Loki + Tempo)
- cd tools/monitoring
- docker compose up -d
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

Schema & Tests
- Validate schemas: python tools/validation/validate_schemas.py
- Run fast tests: pytest -m "unit or contract or component" -q --cov=core --cov=backend --cov-report=term

