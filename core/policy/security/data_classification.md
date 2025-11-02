# Data Classification

Categories of data and handling requirements.

- Public
  - Non-sensitive docs and examples; no restrictions

- Internal
  - Development artifacts and logs (without PII); limited sharing

- Sensitive
  - Credentials, secrets, tokens; never in logs or VCS; encrypt at rest

- Personal/PII
  - Names, emails, identifiers; minimize collection; redact in outputs

- Handling Matrix (examples)
  - Logs: redact secrets/PII; use INFO as default; DEBUG only locally
  - Backups: encrypt at rest; limit retention per environment
