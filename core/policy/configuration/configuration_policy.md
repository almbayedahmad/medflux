# Configuration Policy (Placeholder)

Standards for authoring and loading configuration files.

- Formats
  - Prefer YAML for human-edited configuration; JSON for program output

- Structure
  - Use namespaced keys (e.g., `io.*`, `options.*`)
  - Provide defaults; document required keys

- Environments
  - Support dev/staging/prod overlays; define precedence
  - Do not commit secrets; load from environment or secrets manager

- Validation
  - Validate structure against schemas where applicable
  - Fail fast on missing/invalid keys

- Overrides
  - Allow local developer overrides via `core/policy/rules.local.yaml`
  - Keep machine-specific paths and secrets out of VCS
