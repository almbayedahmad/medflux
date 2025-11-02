# Policy Governance

Defines how policies are authored, reviewed, versioned, and retired.

- Ownership
  - Each policy folder has an implicit owner (team/role). List owners in CODEOWNERS (to be added) and folder README.

- Changes
  - Propose changes via PR with rationale. Link to related ADRs if architectural.
  - Small edits: 1 reviewer from owners. Broad changes: 2+ reviewers including one cross‑team.

- Versioning
  - Track material policy changes in repository CHANGELOG or policy-specific mini-changelog.
  - Use SemVer-like bump on policy docs when automations consume them.

- Sunset
  - Mark deprecated with a note at top; provide replacement doc.
  - Remove after migration window, keeping link stubs for 1 cycle.

- Validation
  - CI should lint policy files (YAML/Markdown) and verify required keys exist where applicable.
