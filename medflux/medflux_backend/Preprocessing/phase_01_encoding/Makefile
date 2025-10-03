PYTHON=python
STAGE_DIR=medflux_backend/Preprocessing/phase_01_encoding

run:
	@if [ -z "$(INPUTS)" ]; then 		echo "Set INPUTS="path1 path2""; exit 1; 	fi
	$(PYTHON) -m medflux_backend.Preprocessing.phase_01_encoding.pipeline_workflow.encoding_cli $(INPUTS) $(if $(NORMALIZE),--normalize,) $(if $(DEST_OUTDIR),--dest-outdir $(DEST_OUTDIR),) $(if $(NEWLINE),--newline $(NEWLINE),) $(if $(ERRORS),--errors $(ERRORS),)

validate: test

test:
	pytest -q $(STAGE_DIR)/tests

format:
	black $(STAGE_DIR)

lint:
	flake8 $(STAGE_DIR)
