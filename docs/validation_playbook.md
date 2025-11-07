Validation Playbook

When to validate
- Input at every public boundary (CLI, API).
- Outputs after each pipeline stage.
- Event/log payloads against the log schema for structured ingest.

Where to validate
- Schemas live in core/validation/contracts/**.
- Stage contracts in core/policy/contracts and core/validation/contracts/stages/**.
- Logging schema in core/logging/log_record.schema.json.

How to validate (local)
- Validate all schemas: python tools/validation/validate_schemas.py
- Verify declared vs runtime schema version: python tools/schema/verify_schema_version.py
- Validate a stage output: python tools/validation/validate_phase.py <phase> output <path> --log-json
- Validate logs in repo: python tools/logs/validate_records.py --root logs --glob "**/*.jsonl" --min-context 0.95

Dry-run and demotions
- Set `MEDFLUX_VALIDATION_DRYRUN=1` to downgrade validation failures to warnings (VL-W001/VL-W002) without raising.
- Demotion rules are defined in `core/policy/validation/validation_rules.yaml` (e.g., demote `additionalProperties` or specific schema paths during iteration).

CI Alignment
- See .github/workflows/ci.yaml jobs: schema-validation and smoke for automated checks.
- Breaking schema changes must accompany a version bump per core/policy/versioning/schema_versioning.md.
