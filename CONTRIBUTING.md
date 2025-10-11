Contributing Guidelines

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
- GitHub Actions runs pre‑commit and a forbidden‑paths check on every push/PR.
- CI fails if files under local OS folders (e.g., `OneDrive/`) or `outputs/` are tracked.

