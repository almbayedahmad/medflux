Validation layer for phase input/output contracts using JSON Schema (draft 2020-12).

Key modules
- errors.py — ValidationError with code and details
- loader.py — loads .json/.yaml schemas
- registry.py — discovers per-phase schema paths under contracts/stages
- validator.py — validate_input/validate_output with Draft202012Validator
- formats.py — custom FormatChecker (uuid, path, run-id)
- decorators.py — @validate_io("phase") wrapper (optional, soft/hard) and payload_from_args()
- policy.py - demotion rules via core/policy/validation/validation_rules.yaml (env: MEDFLUX_VALIDATION_POLICY; legacy MFLUX_VALIDATION_POLICY)

Usage
- Validate a payload manually:
  from core.validation import validate_input, validate_output
  validate_input("phase_00_detect_type", payload)
  validate_output("phase_00_detect_type", result)

- Decorate a function (soft-fail via env MEDFLUX_VALIDATION_SOFT=1; legacy MFLUX_VALIDATION_SOFT=1):
  from core.validation import validate_io
  @validate_io("phase_00_detect_type")
  def run_stage(payload): ...

Schemas live under core/validation/contracts. Override root via MEDFLUX_SCHEMA_ROOT (legacy MFLUX_SCHEMA_ROOT).

Best practices
- Add $id for every schema; keep relative $refs stable
- Prefer $defs for shared shapes (refer via $ref)
- Tighten with minItems, minProperties, enums, patterns
