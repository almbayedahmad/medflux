Branch Protection – Required Checks (Main)

Enable branch protection on the main branch with:
- Require a pull request before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging

Recommended required checks
- CI / Lint (pre-commit): job id lint in .github/workflows/ci.yaml
- CI / Tests (matrix): job id tests in .github/workflows/ci.yaml
  - Optionally require at least the Ubuntu/Python 3.12 job name
- CI / Schema & Docs: job id schema-validation in .github/workflows/ci.yaml
- CI / Policy & Version Checks: job id policy-version in .github/workflows/ci.yaml
- CI / Package Parity: job id package-parity in .github/workflows/ci.yaml
- CI / Smoke CLI & Logs: job id smoke in .github/workflows/ci.yaml
- CI / Integration Tests (API): job id integration in .github/workflows/ci.yaml
- Security / CodeQL: workflow name CodeQL (job analyze)
- Commitlint / commitlint: workflow name Commitlint

Notes
- Matrix jobs appear as separate entries (e.g., Tests (matrix) (ubuntu-latest, 3.12)). You can require specific variants to balance thoroughness and speed.
- To enforce coverage on new code, Codecov patch status is configured at 80% in codecov.yml; also consider enabling Codecov as a required check for PRs.
- Keep “Allow force pushes” and “Allow deletions” disabled for main.

