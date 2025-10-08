# Agent Instructions

This document provides a checklist for automation to ensure deterministic scaffolding and consistent phase development.

## Phase Initialization Checklist

### 1. Pre-Initialization
- [ ] Verify phase requirements
- [ ] Check naming conventions
- [ ] Validate phase order
- [ ] Confirm dependencies
- [ ] Review existing phases

### 2. Directory Structure Creation
- [ ] Create main phase directory
- [ ] Create required subdirectories
- [ ] Create `__init__.py` files
- [ ] Set proper permissions
- [ ] Verify directory structure

### 3. Template File Copying
- [ ] Copy common stage files
- [ ] Copy phase-specific templates
- [ ] Update template placeholders
- [ ] Verify file permissions
- [ ] Check file integrity

### 4. Configuration Setup
- [ ] Create configuration files
- [ ] Set default values
- [ ] Validate configuration syntax
- [ ] Test configuration loading
- [ ] Document configuration options

### 5. Code Generation
- [ ] Generate core functions
- [ ] Generate pipeline workflow
- [ ] Generate schemas
- [ ] Generate tests
- [ ] Generate documentation

### 6. Validation and Testing
- [ ] Run syntax validation
- [ ] Run import tests
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Verify functionality

## File Generation Rules

### Core Functions
- Generate from templates
- Include proper imports
- Add type hints
- Include docstrings
- Add error handling

### Pipeline Workflow
- Generate entry points
- Include orchestration logic
- Add error handling
- Include logging
- Add monitoring

### Schemas
- Generate type definitions
- Include validation rules
- Add documentation
- Include examples
- Add versioning

### Tests
- Generate unit tests
- Include integration tests
- Add test fixtures
- Include test data
- Add test utilities

### Documentation
- Generate README
- Include API documentation
- Add usage examples
- Include troubleshooting
- Add changelog

## Template Processing

### Placeholder Replacement
- `{{PHASE_NAME}}` - Phase display name
- `{{PHASE_ID}}` - Phase identifier
- `{{PHASE_VERSION}}` - Phase version
- `{{CREATED_AT}}` - Creation timestamp
- `{{AUTHOR}}` - Author information
- `{{INPUTS}}` - Input descriptions
- `{{OUTPUTS}}` - Output descriptions
- `{{STANDARD_OUTPUT_PATH}}` - Standard output path
- `{{SAMPLE_OUTPUT_PATH}}` - Sample output path
- `{{SCHEMA_VERSION}}` - Schema version

### Template Validation
- Check all placeholders replaced
- Validate template syntax
- Check file permissions
- Verify file integrity
- Test template loading

## Code Quality Checks

### Syntax Validation
- Python syntax check
- YAML syntax check
- JSON syntax check
- Markdown syntax check
- Configuration validation

### Import Validation
- Check import statements
- Verify module availability
- Test import resolution
- Check circular imports
- Validate dependencies

### Type Checking
- Run type checker
- Check type hints
- Validate type annotations
- Check type compatibility
- Verify type safety

### Linting
- Run code linter
- Check style guidelines
- Validate naming conventions
- Check complexity metrics
- Verify best practices

## Testing Requirements

### Unit Tests
- Test all functions
- Test error cases
- Test edge cases
- Test boundary conditions
- Test type safety

### Integration Tests
- Test module integration
- Test pipeline integration
- Test external dependencies
- Test configuration loading
- Test error handling

### Performance Tests
- Test performance benchmarks
- Test memory usage
- Test CPU usage
- Test I/O performance
- Test scalability

### Security Tests
- Test input validation
- Test output sanitization
- Test access control
- Test data protection
- Test vulnerability scanning

## Documentation Requirements

### Code Documentation
- Function docstrings
- Class docstrings
- Module docstrings
- Type annotations
- Usage examples

### API Documentation
- API endpoints
- Request/response formats
- Error codes
- Authentication
- Rate limiting

### User Documentation
- Installation guide
- Configuration guide
- Usage examples
- Troubleshooting
- FAQ

### Developer Documentation
- Architecture overview
- Development setup
- Testing guide
- Contributing guide
- Code review process

## Configuration Management

### Configuration Files
- Main configuration
- Environment configuration
- Feature flags
- Performance settings
- Security settings

### Configuration Validation
- Schema validation
- Value validation
- Dependency validation
- Environment validation
- Security validation

### Configuration Updates
- Version control
- Change tracking
- Rollback capability
- Migration support
- Validation testing

## Deployment Preparation

### Build Process
- Compile code
- Run tests
- Generate documentation
- Create packages
- Sign artifacts

### Deployment Package
- Include all dependencies
- Include configuration
- Include documentation
- Include tests
- Include utilities

### Deployment Validation
- Test deployment
- Validate configuration
- Test functionality
- Monitor performance
- Check logs

## Monitoring and Observability

### Logging Setup
- Configure log levels
- Set log formats
- Configure log rotation
- Set log destinations
- Add log filtering

### Metrics Collection
- Performance metrics
- Business metrics
- Error metrics
- Usage metrics
- Quality metrics

### Alerting Configuration
- Set alert thresholds
- Configure alert channels
- Set alert rules
- Test alerting
- Monitor alerting

## Security Considerations

### Security Scanning
- Vulnerability scanning
- Dependency scanning
- Code scanning
- Configuration scanning
- Runtime scanning

### Security Configuration
- Access control
- Authentication
- Authorization
- Encryption
- Data protection

### Security Testing
- Penetration testing
- Security testing
- Compliance testing
- Audit testing
- Risk assessment

## Quality Assurance

### Code Review
- Automated review
- Manual review
- Security review
- Performance review
- Documentation review

### Testing Coverage
- Unit test coverage
- Integration test coverage
- End-to-end test coverage
- Performance test coverage
- Security test coverage

### Quality Metrics
- Code quality metrics
- Test quality metrics
- Documentation quality
- Performance metrics
- Security metrics

## Error Handling

### Error Detection
- Input validation
- Output validation
- Runtime errors
- Configuration errors
- Dependency errors

### Error Recovery
- Automatic recovery
- Manual recovery
- Fallback mechanisms
- Retry logic
- Circuit breakers

### Error Reporting
- Error logging
- Error monitoring
- Error alerting
- Error tracking
- Error analysis

## Performance Optimization

### Performance Monitoring
- Response time
- Throughput
- Resource usage
- Error rates
- User experience

### Performance Tuning
- Code optimization
- Configuration tuning
- Resource optimization
- Caching optimization
- Database optimization

### Performance Testing
- Load testing
- Stress testing
- Volume testing
- Spike testing
- Endurance testing

## Maintenance Procedures

### Regular Maintenance
- Dependency updates
- Security patches
- Performance tuning
- Configuration updates
- Documentation updates

### Emergency Maintenance
- Critical bug fixes
- Security patches
- Performance issues
- System failures
- Data corruption

### Maintenance Planning
- Maintenance windows
- Change management
- Risk assessment
- Rollback planning
- Communication planning

## Contact Information

- **Development Team**: {{DEVELOPMENT_TEAM}}
- **QA Team**: {{QA_TEAM}}
- **DevOps Team**: {{DEVOPS_TEAM}}
- **Security Team**: {{SECURITY_TEAM}}
- **Emergency Contact**: {{EMERGENCY_CONTACT}}

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | {{CREATED_AT}} | Initial agent instructions |
