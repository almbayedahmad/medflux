# Agent Workflow

## Overview
Use the consolidated standards in `standards/tree_structure_with_layers_and_rules_v6.yaml` for all development and validation tasks.

## Change Process

### 1. Load Standards
- Load the v6 standards file: `standards/tree_structure_with_layers_and_rules_v6.yaml`
- Apply naming conventions and structure rules from the consolidated standards

### 2. Apply Rules
- Validate the directory tree and verify every required folder exists
- Check module and function names against the naming standards
- Ensure all written content remains in English as required by the language policy
- Forbid "loader" terms in function names

### 3. Run Validation
- Use the v6 validator: `python automation/v6_validator.py --stage-root {stage_path}`
- Execute validation checks using the consolidated standards
- Stop if any validator reports an error

### 4. Update Documentation
- Run documentation automation: `python automation/auto_documentation_update.py --event update --stage {stage_path}`
- Review the generated README and CHANGELOG entries
- Replace placeholder text with real context before finalizing the change

### 5. Commit Changes
- Use the change pipeline: `automation/change_pipeline.yaml`
- Execute the appropriate flow (`on_new_stage`, `on_update_stage`, or `on_delete_stage`)
- Follow git conventions from `standards/git_configuration.md`

### 6. Summarize Work
- Prepare a short report stating the problem, solution, and benefit
- Complete commit template accurately

## Environment Setup

### Runtime Requirements
- Python 3.11 or newer with `pip` available
- Git installed and configured with your user name and email
- Make available (GNU Make on Linux/macOS or make.exe on Windows via MSYS2 or Git Bash)

### Python Dependencies
- Install project packages with `pip install -r requirements.txt` when the file is present
- Ensure PyYAML is available; several automation scripts require it
- Use virtual environments to isolate dependencies and avoid system-wide changes

### Repository Expectations
- Run commands from the repository root unless a script specifies otherwise
- Keep the workspace clean: resolve `git status` noise before starting a new task
- Configure the provided Git hooks with `make hooks-install` so documentation updates run automatically

### Validation
- Before committing, run `make validate STAGE=<path-to-stage>` for any stage you touched
- Execute `make doc-update STAGE=<path> STAGE_NAME=<name> PHASE=<nn>` when documentation needs manual refresh

## Git Configuration

### Git Remote
```
git remote -v
origin  https://github.com/almbayedahmad/medflux.git (fetch)
origin  https://github.com/almbayedahmad/medflux.git (push)
```

Use the standard Git workflow (git status, git commit, git push) from the repository root.

## Smoke Testing

Perform these quick checks before handing off a change for review:

- **Standards validator**: `make validate STAGE=<stage-path>` returns without errors
- **Documentation sync**: `make doc-update ...` produces only expected diffs; changelog entries contain real context
- **Git status**: only the intended files are modified or staged; hooks ran successfully
- **Runtime sanity**: when applicable, execute the stage entry point or a focused unit test to confirm there are no obvious runtime failures
- **Language adherence**: confirm all touched content remains in English and avoids forbidden terms such as "loader"

## Session Policy

Follow these policy steps while collaborating on repository tasks:

1. **Analyze** the current tree before proposing changes. Review outstanding modifications and staged files
2. **Propose** a plan that outlines the intended edits and affected paths
3. **Wait** for confirmation from the requester or reviewer before applying changes
4. **Apply** changes according to the agreed plan, keeping commits focused and reversible
5. **Run** validation and tests using the standards validator and any stage-specific checks
6. **Deliver** a summary detailing the problem, solution, and benefit so stakeholders can record the outcome

Creating new files requires explicit approval per the consolidated standards.

## Tools Available

### Phase Creation
- Use `tools/stage_builder_op/stage_builder_v2.py` to create new phases
- Templates available in `tools/stage_builder_op/templates/`

### Automation
- Change pipeline: `automation/change_pipeline.yaml`
- Documentation updates: `automation/auto_documentation_update.py`
- Validation: `automation/v6_validator.py`

### Standards
- Main standards: `standards/tree_structure_with_layers_and_rules_v6.yaml`
- Environment setup: `standards/environment_setup.md`
- Git configuration: `standards/git_configuration.md`
- Smoke testing: `standards/smoke_testing.md`
