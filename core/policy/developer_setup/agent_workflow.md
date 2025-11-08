# Agent Workflow (Slim)

High-level process to apply standards and deliver changes. For environment setup and detailed checklists, see:
- core/policy/developer_setup/environment_setup.md
- core/policy/developer_setup/development_checklist.md

## Overview
Use the consolidated standards (see <removed: consolidated into codebase and docs>) for structure, naming, and validation.

## Change Process

### 1. Load Standards
- Read architecture and naming standards
- Confirm placement rules and stage structure

### 2. Apply Rules
- Validate directory tree and required folders
- Check module and function names against naming standards
- Enforce English-only hints/text (language policy)
- Forbid "loader" terms in function names

### 3. Run Validation
- Execute validators (structure, naming, language)
- Stop if any validator reports an error

### 4. Update Documentation
- Sync README/CHANGELOG per docs conventions
- Replace placeholders with real context

### 5. Commit Changes
- Follow git conventions (see core/policy/git/)
- Keep commits focused and reversible

### 6. Summarize Work
- Short report: problem, solution, benefit
- Complete commit template accurately

## Smoke Testing
Run quick sanity checks before review:
- Standards validator exits clean
- Docs update produces expected diffs
- Git status shows only intended changes
- If applicable, run a focused unit or stage entry
- Language adherence confirmed; no forbidden terms

## Session Policy
While collaborating on repo tasks:
1) Analyze current tree and changes
2) Propose a plan listing intended edits
3) Wait for confirmation before applying edits
4) Apply changes per plan with focused commits
5) Run validation and tests
6) Deliver a concise summary of outcome

## Tools and References
- Standards: <removed: consolidated into codebase and docs>
- Docs conventions: core/policy/documentation/docs_conventions.yaml
- Language policy: core/policy/documentation/language_policy.yaml
- Naming standards: core/policy/documentation/naming_standards.md
- Git: core/policy/git/README.md
- Testing policies: core/policy/testing/README.md
