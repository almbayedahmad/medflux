# Agent Instructions - Environment and Requirements

Set up and maintain a working environment that keeps the automation tools reliable.

## Runtime
- Python 3.11 or newer with `pip` available.
- Git installed and configured with your user name and email.
- Make available (GNU Make on Linux/macOS or make.exe on Windows via MSYS2 or Git Bash).

## Python Dependencies
- Install project packages with `pip install -r requirements.txt` when the file is present.
- Ensure PyYAML is available; several automation scripts require it.
- Use virtual environments to isolate dependencies and avoid system-wide changes.

## Repository Expectations
- Run commands from the repository root unless a script specifies otherwise.
- Keep the workspace clean: resolve `git status` noise before starting a new task.
- Configure the provided Git hooks with `make hooks-install` so documentation updates run automatically.

## Validation
- Before committing, run `make validate STAGE=<path-to-stage>` for any stage you touched.
- Execute `make doc-update STAGE=<path> STAGE_NAME=<name> PHASE=<nn>` when documentation needs manual refresh.
