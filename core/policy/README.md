Top-level policies centralized for the repository. This folder is the single source of truth for governance; code in core/backend/apps should read policies from here.

Structure
- documentation/
  - docs_conventions.yaml - Documentation structure, formatting, and review.
  - language_policy.yaml - English-only documentation/code hints policy.
  - naming_standards.md - File, function, and directory naming rules.
  - coding_standards.md - Code style, linting, and docstrings.
- validation/
  - validation_rules.yaml — Global validation criteria and ranges.
  - text_normalization.yaml — Encoding, BOM, newline, and error policies.
- contracts/
  - stage_contract.yaml — Contract template for inter-stage inputs/outputs.
- observability/
  - kpis.yaml - Cross-stage KPIs and reporting/alerting guidance.
  - logging_config.yaml - Central logging configuration.
  - logging_policy.md - Log levels, content, and retention guidance.
  - logging_fields.md - Required log fields for traceability.
  - metrics_traces_conventions.md - Metric and trace naming + tags.
- versioning/
  - versioning_policy.md - SemVer policy and release process.
  - schema_versioning.md - Schema lifecycle and migration rules.
- git/
  - commit_conventions.md - Conventional commits and guidelines.
  - git_rules.md - Git workflow standards.
  - git_configuration.md - Git configuration setup.
  - branching_strategy.md - Branch names and flows.
- developer_setup/
  - environment_setup.md - Environment provisioning guidance.
  - agent_workflow.md - Agent workflow and operating procedures.
  - phase_scaffolding_guide.md - Step-by-step scaffolding instructions.
  - development_checklist.md - Pre/post merge and quality checklist.
- testing/
  - smoke_testing.md - Smoke test process and criteria.
- architecture/
  - Architecture references consolidated into per-component READMEs and code; legacy tree file removed.
  - phase_creation_guide.md - How to create phases following standards.
  - adr_template.md - Architecture decision record template.
- security/
  - security_policy.md - Secure coding, dependencies, incidents.
  - secrets_management.md - Handling secrets across environments.
  - data_privacy.md - PII/GDPR guardrails and retention.
  - access_control.md - Roles, branch protections, secrets access.
  - data_classification.md - Data categories and handling.
- ci_cd/
  - ci_cd_policy.md - Branch protections, tagging, environments.
  - required_checks.md - Lint/tests/security/docs gates.
- configuration/
  - configuration_policy.md - Config structure, validation, overlays.
- dependencies/
  - dependency_management.md - Pinning, updates, scanning.
- policy_governance.md - How policy changes are proposed and approved.
- policy_loader.md - How code loads policies and applies overrides.
- rules.local.yaml — Local developer overrides (not committed).

Notes
- These are copies of existing backend standards placed here for centralization. Backend references will be updated to point here during its restructuring.
- Do not place secrets or environment-specific values in this directory; use rules.local.yaml for local overrides and keep it out of VCS.

Directory Index
- documentation/ → documentation/README.md
- validation/ → validation/README.md
- contracts/ → contracts/README.md
- observability/ → observability/README.md
- versioning/ → versioning/README.md
- git/ → git/README.md
- developer_setup/ → developer_setup/README.md
- testing/ → testing/README.md
- architecture/ → architecture/README.md
