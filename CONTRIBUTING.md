# Contributing to Blocking Responses API

Thank you for your interest in contributing to the Blocking Responses API! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct that fosters an open and welcoming environment. Please read and follow our Code of Conduct.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please:
1. **Search existing issues** to see if the problem has already been reported
2. **Use the bug report template** to provide necessary information
3. **Include detailed reproduction steps** and environment information

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
1. **Search existing issues** for similar suggestions
2. **Use the feature request template** to describe your idea
3. **Provide clear use cases** and explain the benefits

### Pull Requests

#### Before Submitting

1. **Fork the repository** and create your branch from `main`
2. **Test your changes** thoroughly
3. **Update documentation** as needed
4. **Follow code style guidelines**

#### Submission Process

1. **Fill out the pull request template** completely
2. **Link to related issues** using "Fixes #123" format
3. **Ensure all tests pass** and add new tests for new features
4. **Request review** from maintainers

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git
- OpenAI API key (for testing LLM features)

### Local Development

1. **Clone the repository**
   ```bash
   git clone git@github.com:adorosario/blocking-responses-poc.git
   cd blocking-responses-poc
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Start services**
   ```bash
   ./docker-run.sh dev
   ```

4. **Run tests**
   ```bash
   make test
   ```

### Code Style

#### Python Code Guidelines

- **Follow PEP 8** with line length limit of 120 characters
- **Use type hints** for function parameters and return values
- **Write docstrings** for all public functions and classes
- **Use meaningful variable names** and avoid abbreviations
- **Keep functions focused** and under 50 lines when possible

#### Code Formatting

```bash
# Install development dependencies
pip install flake8 mypy black isort

# Format code
black app.py test_app.py
isort app.py test_app.py

# Check style
flake8 app.py test_app.py --max-line-length=120
mypy app.py --ignore-missing-imports
```

### Testing Guidelines

#### Test Requirements

- **All new features** must include comprehensive tests
- **Bug fixes** should include regression tests
- **Tests should be fast** and not require external services
- **Mock external dependencies** (OpenAI API calls, etc.)

#### Running Tests

```bash
# Run all tests
pytest test_app.py -v

# Run specific test categories
pytest test_app.py::TestRiskPatterns -v
pytest test_app.py::TestAPI -v

# Run with coverage
pytest test_app.py --cov=app --cov-report=html
```

#### Writing Tests

- Use descriptive test names: `test_ssn_pattern_blocks_response`
- Test both positive and negative cases
- Include edge cases and boundary conditions
- Mock external API calls

Example test structure:
```python
class TestNewFeature:
    def test_feature_with_valid_input(self):
        # Arrange
        input_data = {"test": "data"}
        
        # Act
        result = feature_function(input_data)
        
        # Assert
        assert result.success is True
        assert result.value == expected_value
```

## Security Guidelines

### Reporting Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

Instead:
1. Email security concerns to [maintainer email]
2. Include detailed information about the vulnerability
3. Allow time for assessment and patching before public disclosure

### Security Best Practices

- **Never commit secrets** (API keys, passwords) to the repository
- **Validate all inputs** and sanitize outputs
- **Use secure defaults** for configuration
- **Log security events** without exposing sensitive data
- **Follow principle of least privilege**

### Security Review Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] Output sanitization applied
- [ ] Error messages don't leak sensitive information
- [ ] Authentication and authorization properly implemented
- [ ] Dependencies are up to date and secure

## Documentation Standards

### Documentation Requirements

- **Update README.md** for user-facing changes
- **Update CLAUDE.md** for development changes
- **Update API documentation** for endpoint changes
- **Add inline comments** for complex logic
- **Update CHANGELOG.md** for all changes

### Documentation Style

- **Use clear, concise language**
- **Include examples** for complex features
- **Provide step-by-step instructions**
- **Keep documentation up to date** with code changes

## Commit Message Guidelines

### Commit Message Format

```
type(scope): brief description

Longer description if needed

- Additional details
- Breaking changes noted
- References to issues

Fixes #123
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no logic changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(api): add email risk pattern detection

- Added regex pattern for email detection
- Configurable risk score (default 0.5)
- Updated risk assessment tests

Fixes #45

fix(docker): resolve CORS configuration issue

- Fixed pydantic settings parsing for CORS origins
- Updated docker-compose environment variables
- Added validation for CORS configuration

Fixes #67
```

## Performance Guidelines

### Performance Considerations

- **Minimize latency impact** of security features
- **Use efficient algorithms** for pattern matching
- **Implement proper caching** where appropriate
- **Monitor resource usage** in production
- **Profile performance-critical paths**

### Performance Testing

- **Benchmark new features** against baseline
- **Test with realistic workloads**
- **Monitor memory usage** and garbage collection
- **Test concurrent request handling**

## Release Process

### Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backward compatible)
- **PATCH** version for bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Docker images built and tested
- [ ] Release notes prepared

## Getting Help

### Resources

- **Documentation**: Check README.md and CLAUDE.md
- **Issues**: Search existing issues for solutions
- **Discussions**: Use GitHub Discussions for questions
- **Code**: Review existing code for patterns and examples

### Communication

- **Be respectful** and constructive in all communications
- **Provide context** when asking questions
- **Share relevant details** about your environment and use case
- **Follow up** on issues and discussions

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project documentation for major features

Thank you for contributing to the Blocking Responses API! Your efforts help make AI systems safer and more reliable.