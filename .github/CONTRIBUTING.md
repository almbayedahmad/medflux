Contributing Guidelines

Developer Tools
- See `tools/TOOLS.md` for scripts and utilities grouped by function (versioning, schema, validation, logs, monitoring, CI).

Branching and Reviews
- Use short‑lived feature branches (e.g., feat/x, fix/y).
- Open Pull Requests into `main`; avoid committing directly to `main`.
- Delete feature branches on merge to keep the repo tidy.

Branch Protections (enable in GitHub UI)
- Settings → Branches → Add rule for `main`:
  - Require a pull request before merging (1+ approval recommended).
  - Dismiss stale approvals on new commits.
  - Require status checks to pass (enable the CI workflow checks).
  - Restrict who can push to matching branches (optional).

Local Git Hygiene
- Prune stale remotes regularly: `git fetch --prune`.
- Rebase small, focused commits per PR.

Pre‑commit Hooks
- Install once: `pip install pre-commit`
- Enable in this repo: `pre-commit install`
- Run manually: `pre-commit run --all-files`

What Hooks Enforce
- No commits to `main` (use feature branches).
- No large files (>2MB) added by mistake.
- No merge conflicts, private keys, or trailing whitespace.
- Valid YAML and normalized line endings.

CI Workflow
- Checks run on every push/PR:
  - pre-commit (format, lint, no large files/secrets)
  - Tests + coverage (project ≥ 80%) across a matrix
  - Codecov (patch ≥ 80%)
  - Schema validation + docs generation checks
  - Schema compatibility guard vs last tag (breaking changes require MAJOR bump)
  - Packaging parity (wheel version matches VERSION)
  - Smoke + integration tests

Conventional Commits
- Use `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`
- Commitlint runs in CI.

Releases
- Bump `core/versioning/VERSION`, tag `vX.Y.Z`, and push; or
- Use the manual Release workflow (GitHub Actions) to bump and tag.

Required status checks (suggested)
- Lint (pre-commit), Tests (matrix), Schema & Docs, Policy & Version Checks,
  Package Parity, Smoke, Integration, CodeQL, Commitlint
  (see docs/BRANCH_PROTECTION.md for exact job names).
