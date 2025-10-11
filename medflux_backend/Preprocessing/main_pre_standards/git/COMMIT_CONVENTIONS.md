# Commit Conventions

This document defines the structured commit message format and conventions for the {{PHASE_NAME}} phase.

## Commit Message Format

### Structure
```
<type>(<repo>/<phase>_<stage>): <summary>

- Problem: <what problem this solves>
- Solution: <how this solves it>
- Benefit: <what benefit this provides>

Refs: <issue numbers>
```

### Header Format
```
<type>(<scope>): <description>
```

- **type**: Type of change (see types below)
- **scope**: Repository and phase identifier
- **description**: Brief description of the change

### Body Format
```
- Problem: <what problem this solves>
- Solution: <how this solves it>
- Benefit: <what benefit this provides>
```

### Footer Format
```
Refs: <issue numbers>
```

## Commit Types

### Primary Types
- **feat**: New features (minor version bump)
- **fix**: Bug fixes (patch version bump)
- **refactor**: Code refactoring (patch version bump)
- **docs**: Documentation changes (patch version bump)
- **test**: Test additions or changes (patch version bump)
- **chore**: Maintenance tasks (patch version bump)

### Secondary Types
- **perf**: Performance improvements (patch version bump)
- **build**: Build system changes (patch version bump)
- **ci**: CI/CD changes (patch version bump)
- **style**: Code style changes (patch version bump)
- **revert**: Revert previous commits (patch version bump)

### Breaking Changes
- **breaking**: Breaking changes (major version bump)
- Use `BREAKING CHANGE:` in footer for breaking changes

## Scope Format

### Repository Scope
- **medflux**: Main repository
- **preprocessing**: Preprocessing module
- **phase_XX_<stage>**: Specific phase

### Examples
- `medflux/phase_02_readers`
- `preprocessing/phase_01_detect`
- `medflux/phase_03_normalize`

## Description Guidelines

### Format
- Use imperative mood ("add feature" not "added feature")
- Start with lowercase letter
- No period at the end
- Maximum 50 characters
- Be descriptive but concise

### Examples
- ✅ `add OCR table detection`
- ✅ `fix memory leak in PDF processing`
- ✅ `refactor configuration loading`
- ❌ `Added OCR table detection`
- ❌ `Fixed memory leak in PDF processing`
- ❌ `Refactored configuration loading`

## Body Guidelines

### Problem Section
- Describe the problem being solved
- Be specific and clear
- Include context if necessary
- Use present tense

### Solution Section
- Describe how the problem is solved
- Be technical but clear
- Include key implementation details
- Use past tense

### Benefit Section
- Describe the benefit of the change
- Focus on user impact
- Be measurable when possible
- Use present tense

## Examples

### Feature Addition
```
feat(medflux/phase_02_readers): add OCR table detection

- Problem: Tables in scanned documents were not being detected, leading to poor data extraction
- Solution: Integrated table detection algorithm with OCR processing pipeline
- Benefit: Improved accuracy for tabular data extraction by 25%

Refs: #123, #124
```

### Bug Fix
```
fix(medflux/phase_02_readers): resolve memory leak in PDF processing

- Problem: Memory usage increased over time during batch processing, causing system instability
- Solution: Added proper resource cleanup and garbage collection in PDF processing loop
- Benefit: Stable memory usage during long-running operations

Refs: #125
```

### Refactoring
```
refactor(medflux/phase_02_readers): simplify configuration loading

- Problem: Configuration loading was complex and hard to maintain
- Solution: Extracted configuration logic into separate module with clear interfaces
- Benefit: Easier to maintain and extend configuration system

Refs: #126
```

### Documentation
```
docs(medflux/phase_02_readers): update API documentation

- Problem: API documentation was outdated and incomplete
- Solution: Updated all API documentation with current examples and usage patterns
- Benefit: Better developer experience and reduced support requests

Refs: #127
```

### Breaking Change
```
breaking(medflux/phase_02_readers): change OCR output format

- Problem: OCR output format was inconsistent and hard to parse
- Solution: Standardized OCR output format with new schema
- Benefit: Consistent and predictable OCR output format

BREAKING CHANGE: OCR output format changed from legacy format to new schema
Refs: #128
```

## Special Cases

### Merge Commits
```
merge(medflux/phase_02_readers): merge feature/ocr-improvements

- Problem: Feature branch needs to be integrated into main branch
- Solution: Merged feature/ocr-improvements branch into main
- Benefit: OCR improvements now available in main branch

Refs: #129
```

### Revert Commits
```
revert(medflux/phase_02_readers): revert OCR table detection

- Problem: OCR table detection caused performance issues
- Solution: Reverted commit abc123 that added OCR table detection
- Benefit: Restored stable performance

Refs: #130
```

### Hotfix Commits
```
fix(medflux/phase_02_readers): critical security fix

- Problem: Security vulnerability in PDF processing
- Solution: Applied security patch to PDF processing module
- Benefit: Eliminated security vulnerability

Refs: #131
```

## Validation Rules

### Automated Checks
- **Length**: Header maximum 50 characters
- **Format**: Must match regex pattern
- **Type**: Must be valid commit type
- **Scope**: Must be valid scope format

### Manual Checks
- **Clarity**: Description is clear and understandable
- **Completeness**: All sections are filled out
- **Accuracy**: Information is accurate and truthful
- **Relevance**: All information is relevant to the change

## Tools and Automation

### Pre-commit Hooks
- **Commit Message Lint**: Validate commit message format
- **Conventional Commits**: Enforce conventional commit format
- **Length Check**: Ensure appropriate message length

### CI/CD Integration
- **Changelog Generation**: Auto-generate changelog from commits
- **Version Bumping**: Auto-bump version based on commit types
- **Release Notes**: Auto-generate release notes

### IDE Integration
- **Commit Templates**: Provide commit message templates
- **Validation**: Real-time validation of commit messages
- **Suggestions**: Suggest commit types and scopes

## Best Practices

### Writing Good Commits
1. **Be Specific**: Describe exactly what changed
2. **Be Clear**: Use clear, understandable language
3. **Be Complete**: Include all necessary information
4. **Be Consistent**: Follow the same format every time

### Commit Frequency
1. **Commit Often**: Make small, logical commits
2. **Commit Early**: Don't wait for perfect code
3. **Commit Clean**: Ensure code compiles and tests pass
4. **Commit Atomic**: One logical change per commit

### Commit History
1. **Clean History**: Use rebase to clean up history
2. **Logical Order**: Order commits logically
3. **Meaningful Messages**: Write meaningful commit messages
4. **Avoid Merge Commits**: Use rebase when possible

## Troubleshooting

### Common Issues
1. **Message Too Long**: Shorten description or move details to body
2. **Invalid Type**: Use correct commit type
3. **Missing Scope**: Include appropriate scope
4. **Format Issues**: Follow the exact format specified

### Recovery
1. **Amend Last Commit**: Use `git commit --amend`
2. **Interactive Rebase**: Use `git rebase -i` for multiple commits
3. **Reset and Recommit**: Use `git reset` for major changes
4. **Revert Commits**: Use `git revert` for problematic commits

## Training and Resources

### Required Training
- **Commit Message Format**: Understanding the format
- **Commit Types**: Knowing when to use each type
- **Best Practices**: Writing good commit messages
- **Tools**: Using commit message tools

### Resources
- **Conventional Commits**: Specification and examples
- **Git Documentation**: Official git documentation
- **Best Practices**: Industry best practices
- **Tools**: Commit message tools and extensions

## Contact Information

- **Technical Lead**: {{TECHNICAL_LEAD}}
- **Git Administrator**: {{GIT_ADMIN}}
- **Emergency Contact**: {{EMERGENCY_CONTACT}}

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | {{CREATED_AT}} | Initial commit conventions |
