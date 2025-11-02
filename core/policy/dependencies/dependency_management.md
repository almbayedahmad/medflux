# Dependency Management Policy (Placeholder)

Guidelines for adding, pinning, and updating dependencies.

- Pinning
  - Pin production dependencies; allow ranges only for dev tooling
  - Use lockfiles where supported; review diffs in PR

- Adding Packages
  - Prefer standard library and existing utilities first
  - Justify new runtime deps (size, security, maintenance)

- Updates
  - Schedule regular updates (monthly/quarterly)
  - Patch security updates promptly
  - Test impact via smoke/integration suites

- Scanning
  - Run SCA in CI; track and remediate CVEs
  - Avoid deprecated or unmaintained packages
