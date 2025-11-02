# Secrets Management Policy (Placeholder)

Principles and practices for handling secrets and credentials.

- Storage
  - Use environment variables or a secrets manager; never commit secrets
  - Keep `.env` files out of VCS; prefer `ENV.sample` templates
  - Scope secrets per environment (dev/staging/prod)

- Usage
  - Load secrets at runtime; avoid hardcoding
  - Pass only what is needed to subcomponents (least privilege)
  - Rotate and revoke regularly; time-limit tokens when possible

- Tooling
  - Enable secrets scanning in CI
  - Provide helpers to load and validate required secrets
