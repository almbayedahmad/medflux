# Access Control (RBAC) Policy

Defines roles and permissions for repository, CI, and secrets.

- Roles (examples)
  - Maintainer: approves policy changes, protects branches, manages secrets
  - Reviewer: approves code changes in owned areas
  - Contributor: opens PRs, follows policies

- Branch Protection
  - Require reviews for `main` and release branches; block force-push
  - Require status checks (see ci_cd/required_checks.md)

- Secrets Access
  - Scope CI secrets by environment; restrict write access to release workflows
  - Rotate credentials; audit usage periodically

- Policy Approval
  - Policy documents in `core/policy` require owner review (CODEOWNERS)
