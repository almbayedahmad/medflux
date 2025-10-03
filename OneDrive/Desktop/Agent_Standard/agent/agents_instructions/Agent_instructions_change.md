# Agent Instructions - Change Workflow

These instructions explain how the agent enforces the standards and executes the change pipeline.

## Steps

1. **Load every standards file (`standards/`)**
   - 10_tree_structure.yaml
   - 20_naming_standards.yaml
   - 25_language_policy.yaml
   - 30_stage_contract.yaml
   - 40_generation_rules.yaml
   - 50_git_conventions.yaml
   - 60_docs_conventions.yaml
   - 70_validation_rules.yaml
   - 80_kpis.yaml
   - 90_session_policy.yaml

2. **Apply the standards**
   - Validate the directory tree.
   - Check file and function naming rules.
   - Ensure all required folders exist.
   - Confirm all hints/text remain in English per the language policy.

3. **Run the change pipeline**
   - Read `agent/agents_tasks/change_op/change_pipeline.yaml`.
   - Execute tasks according to the event type:
     - `on_new_stage` when a stage is created.
     - `on_update_stage` when a stage is modified.
     - `on_delete_stage` when a stage is removed.

4. **Update documentation automatically**
   - The pipeline calls `agent/agents_tasks/change_op/auto_documentation_update.py` to synchronise the stage README/CHANGELOG and the files under `main_documantion/`.
   - Manual usage: `make doc-update STAGE=path/to/stage PHASE=03 STAGE_NAME=merge EVENT=update CHANGELOG=path/to/stage/CHANGELOG.md`.
   - Review the generated entries and replace the “Why it was needed” / “Result” placeholders with real context before finalising a change.

5. **Provide a summary**
   - Produce a concise report listing the problem, solution, and benefit for every change.
