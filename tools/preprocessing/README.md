# Preprocessing Scaffolding Tools

This directory hosts automation that helps bootstrap new preprocessing phases.

## Phase Generator

Use `phase_generator.py` to create a phase with the standard directory layout:

```bash
python tools/preprocessing/phase_generator.py 03 segment
```

The script mirrors the folder and naming rules defined in:
- `<removed: consolidated into codebase and docs>`
- `core/policy/developer_setup/phase_scaffolding_guide.md`
- `core/policy/documentation/naming_standards.md`

Always load the policies from `core/policy/` before modifying the generated files.
