PYTHON=python
STAGE_DIR=medflux_backend/Preprocessing/phase_00_detect_type

run:
	$(PYTHON) -m medflux_backend.Preprocessing.phase_00_detect_type.pipeline_workflow.detect_type_cli $(INPUTS)

validate: test

test:
	pytest -q $(STAGE_DIR)/tests

format:
	black $(STAGE_DIR)

lint:
	flake8 $(STAGE_DIR)
