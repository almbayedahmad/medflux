Testing policies for fast, reliable quality gates.

- Scope
  - Smoke testing expectations and process
  - Minimal integration checks for CI gating
  - What to measure and how to decide pass/fail

- Start Here
  - core/policy/testing/smoke_testing.md

- Suggested CI Integration
  - Run smoke tests on every PR and before release tags
  - Fail the pipeline on policy breaches (see related policies)

- Related Policies
  - Validation rules: core/policy/validation/validation_rules.yaml
  - Stage contracts: core/policy/contracts/stage_contract.yaml
  - KPIs (quality/latency thresholds): core/policy/observability/kpis.yaml
  - Logging config: core/policy/observability/logging_config.yaml
  - Docs conventions (release notes): core/policy/documentation/docs_conventions.yaml
  - Versioning policy (release gates): core/policy/versioning/versioning_policy.md
