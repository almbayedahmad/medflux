# Stage Builder

This package builds a new stage (`phase_XX_<stage>`) that complies with the shared standards.

## Key files
- **stage_builder_v2.py**: CLI that reads a manifest and generates the stage structure.
- **stage_builder_manifest_template.yaml**: Starter manifest you can copy and fill in.

## Usage
1. Copy `stage_builder_manifest_template.yaml` to a new file such as `my_stage_manifest.yaml`.
2. Update the values (`product_root`, `domain_root`, `phase_number`, `stage_name`, `features`, `generate`).
3. Run the builder:
   ```bash
   python agent/agents_tasks/stage_builder_op/stage_builder_v2.py \
     --manifest my_stage_manifest.yaml \
     --standards-dir agent/agents_rules \
     --templates agent/agents_tasks/stage_builder_op/templates \
     --base-dir products/my_product \
     --domain ingestion \
     --validate
   ```
   The `--validate` flag runs the standards validator immediately after generation.
4. The new stage appears under `products/my_product/ingestion/phase_XX_<stage_name>/` with the generated files and folders.

After generation you can run `make doc-update STAGE=agent/stages_demo/ingestion/phase_03_merge STAGE_NAME=merge PHASE=03 EVENT=update` to sync the documentation entry.
