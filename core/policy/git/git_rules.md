# Git Rules and Guidelines

This document outlines the git workflow, branching strategy, and collaboration rules for the {{PHASE_NAME}} phase.

## Branching Strategy

### Main Branches
- **main**: Production-ready code
- **develop**: Integration branch for features
- **stage/phase_XX_<stage>**: Stage-specific development branch

### Feature Branches
- **feat/phase_XX_<stage>/<short-name>**: New features
- **fix/phase_XX_<stage>/<short-name>**: Bug fixes
- **refactor/phase_XX_<stage>/<short-name>**: Code refactoring
- **docs/phase_XX_<stage>/<short-name>**: Documentation updates

### Release Branches
- **release/vX.Y.Z**: Release preparation
- **hotfix/vX.Y.Z**: Critical fixes

## Commit Message Format

### Structure
```
<type>(<repo>/<phase>_<stage>): <summary>

- Problem: <what problem this solves>
- Solution: <how this solves it>
- Benefit: <what benefit this provides>

Refs: <issue numbers>
```

### Types
- **feat**: New features
- **fix**: Bug fixes
- **refactor**: Code refactoring
- **docs**: Documentation changes
- **test**: Test additions or changes
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **build**: Build system changes
- **ci**: CI/CD changes

### Examples
```
feat(medflux/phase_02_readers): add OCR table detection

- Problem: Tables in scanned documents were not being detected
- Solution: Integrated table detection algorithm with OCR processing
- Benefit: Improved accuracy for tabular data extraction

Refs: #123, #124
```

```
fix(medflux/phase_02_readers): resolve memory leak in PDF processing

- Problem: Memory usage increased over time during batch processing
- Solution: Added proper resource cleanup and garbage collection
- Benefit: Stable memory usage during long-running operations

Refs: #125
```

## Pull Request Process

### Before Creating PR
1. **Code Quality**: Ensure code follows style guidelines
2. **Tests**: All tests must pass
3. **Documentation**: Update relevant documentation
4. **Commit History**: Clean, logical commit history

### PR Requirements
1. **Title**: Match main commit message
2. **Description**: Include problem, solution, and benefit
3. **Impact Scope**: Specify if breaking changes
4. **Validation**: List tests and validators run
5. **Screenshots**: For UI changes
6. **Checklist**: Complete all required items

### PR Template
```markdown
## Title
<PR title matching main commit>

## Problem -> Solution -> Benefit
- **Problem**: <what problem this solves>
- **Solution**: <how this solves it>
- **Benefit**: <what benefit this provides>

## Impact Scope
- [ ] Breaking change (requires major version bump)
- [ ] Non-breaking change
- [ ] Documentation only
- [ ] Test only

## Validation
- [ ] All tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Performance tested
- [ ] Security reviewed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
- [ ] Ready for merge
```

## Code Review Guidelines

### Reviewers
- **Required**: Technical lead
- **Optional**: Peer developer
- **Specialized**: Security, performance, UX experts

### Review Criteria
1. **Functionality**: Does it work as intended?
2. **Code Quality**: Is the code clean and maintainable?
3. **Performance**: Are there performance implications?
4. **Security**: Are there security concerns?
5. **Testing**: Is the code adequately tested?
6. **Documentation**: Is documentation updated?

### Review Process
1. **Initial Review**: Within 24 hours
2. **Feedback**: Provide constructive feedback
3. **Iteration**: Address feedback and re-request review
4. **Approval**: Minimum 2 approvals required
5. **Merge**: After all approvals and checks pass

## Conflict Resolution

### Merge Conflicts
1. **Identify**: Locate conflicting files
2. **Understand**: Understand both changes
3. **Resolve**: Choose appropriate resolution
4. **Test**: Ensure resolution works
5. **Commit**: Commit the resolution

### Disagreements
1. **Discuss**: Open discussion in PR comments
2. **Escalate**: Involve technical lead if needed
3. **Document**: Document decision rationale
4. **Learn**: Use as learning opportunity

## Best Practices

### Commit Practices
- **Atomic Commits**: One logical change per commit
- **Frequent Commits**: Commit often, push regularly
- **Clear Messages**: Write descriptive commit messages
- **Test Before Commit**: Ensure tests pass locally

### Branch Practices
- **Short-lived Branches**: Keep feature branches small
- **Regular Updates**: Sync with main branch regularly
- **Clean History**: Use rebase to clean up history
- **Delete After Merge**: Remove merged branches

### Collaboration Practices
- **Communication**: Communicate changes and issues
- **Documentation**: Keep documentation up-to-date
- **Testing**: Write tests for new functionality
- **Review**: Participate in code reviews

## Emergency Procedures

### Hotfix Process
1. **Create Branch**: `hotfix/vX.Y.Z`
2. **Fix Issue**: Implement minimal fix
3. **Test**: Thoroughly test the fix
4. **Review**: Fast-track review process
5. **Merge**: Merge to main and develop
6. **Deploy**: Deploy immediately
7. **Document**: Document the hotfix

### Rollback Process
1. **Identify**: Identify problematic commit
2. **Create Revert**: Create revert commit
3. **Test**: Test the revert
4. **Review**: Review the revert
5. **Merge**: Merge revert to main
6. **Deploy**: Deploy the revert
7. **Investigate**: Investigate root cause

## Tools and Automation

### Pre-commit Hooks
- **Code Formatting**: Automatic code formatting
- **Linting**: Code quality checks
- **Testing**: Run tests before commit
- **Security**: Security vulnerability checks

### CI/CD Integration
- **Automated Testing**: Run tests on every PR
- **Code Quality**: Automated code quality checks
- **Security Scanning**: Automated security scans
- **Deployment**: Automated deployment pipeline

### Monitoring
- **Commit Activity**: Track commit patterns
- **Review Metrics**: Monitor review times
- **Quality Metrics**: Track code quality trends
- **Performance**: Monitor build and test performance

## Training and Resources

### Required Training
- **Git Fundamentals**: Basic git operations
- **Branching Strategy**: Understanding branch workflow
- **Code Review**: Effective code review practices
- **Conflict Resolution**: Handling merge conflicts

### Resources
- **Git Documentation**: Official git documentation
- **Best Practices**: Industry best practices
- **Tools**: Git tools and extensions
- **Troubleshooting**: Common issues and solutions

## Contact Information

- **Technical Lead**: {{TECHNICAL_LEAD}}
- **Git Administrator**: {{GIT_ADMIN}}
- **Emergency Contact**: {{EMERGENCY_CONTACT}}

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | {{CREATED_AT}} | Initial git rules and guidelines |
