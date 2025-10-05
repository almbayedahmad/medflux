# Readers stage configuration

This directory holds configuration artifacts consumed by the readers phase:

- `stage.yaml` (plus `stage.meta.yaml` and `stage_schema.yaml`) provide pipeline wiring for the stage connector.
- `profiles/` now contains the environment-specific reader settings (`readers.yaml`, `readers.dev.yaml`, `readers.staging.yaml`) that feed `config.runtime_config.CFG`.
- Legacy loaders still fall back to the root `configs/` directory, but new configurations should live in `profiles/`.
