# Main Preprocessing Scaffolding

`backend/Preprocessing/main_pre_standards/` now serves a single purpose: it hosts the phase generator and any helper code needed to bootstrap new phases. All governance documents, policies, and templates are maintained centrally under `core/policy/`.

## Contents

```
main_pre_standards/
└── development/
    └── phase_generator.py        # Creates the minimal phase skeleton
```

## Creating a New Phase

Use the generator to scaffold a phase with the standard folder layout:

```bash
python main_pre_standards/development/phase_generator.py 03 segment
```

The script mirrors the layout and naming conventions defined in:

- `core/policy/architecture/tree_structure_standard.yaml`
- `core/policy/documentation/naming_standards.md`
- `core/policy/developer_setup/phase_scaffolding_guide.md`

## Where to Find Policies

| Topic            | Location in `core/policy/`                                     |
| ---------------- | -------------------------------------------------------------- |
| Architecture     | `architecture/tree_structure_standard.yaml`                    |
| Developer setup  | `developer_setup/` (workflow, checklists, commenting policy)   |
| Documentation    | `documentation/docs_conventions.yaml`, `documentation/...`     |
| Git + versioning | `git/commit_conventions.md`, `versioning/versioning_policy.md` |
| Contracts        | `contracts/stage_contract.yaml`                                |
| Observability    | `observability/` (logging, KPIs, redaction)                    |

Always load the policies from `core/policy/` before modifying or generating code. `main_pre_standards/` is intentionally minimal so updates to policy files happen in one location.

## Support

- Review `core/policy/developer_setup/phase_scaffolding_guide.md` for the step-by-step scaffold process.
- Use `phase_generator.py` for new phases; avoid copying legacy templates.
- If the generator needs enhancements, update it here and document the change in `core/policy/`.
