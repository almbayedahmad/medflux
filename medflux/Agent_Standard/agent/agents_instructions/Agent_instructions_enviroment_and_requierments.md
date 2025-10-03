
# Agent Instructions – Change Workflow

These instructions explain how the agent enforces the standards and executes the change pipeline.

## Steps

1. **Load every standards file (`standards/`)**
   - 10_tree_structure.yaml
   - 20_naming_standards.yaml
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

3. **Run the change pipeline**
   - Read `agent/agents_tasks/change_op/change_pipeline.yaml`.
   - Execute tasks according to the event type:
     - `on_new_stage` when a stage is created.
     - `on_update_stage` when a stage is modified.
     - `on_delete_stage` when a stage is removed.

4. **Update the documentation automatically**
   - Run `agent/agents_tasks/change_op/auto_documentation_update.py` if it has not been triggered by the pipeline.

5. **Provide a summary**
   - Produce a concise report listing the problem, solution, and benefit for every change.
