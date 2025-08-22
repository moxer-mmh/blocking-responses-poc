# Testing Guide

This document provides comprehensive information about testing the Blocking Responses API system.

## Test Suite Overview

✅ **Current Status: 16/16 tests passing (100% success rate)**

The test suite validates all core functionality including pattern detection, compliance scoring, API endpoints, and Microsoft Presidio integration.

## Running Tests

### Docker-based Testing (Recommended)

```bash
# Run complete test suite
sudo docker compose run --rm api pytest test_app_basic.py -v

# Run with coverage report
sudo docker compose run --rm api pytest test_app_basic.py --cov=app --cov-report=html

# Run specific test category
sudo docker compose run --rm api pytest test_app_basic.py::TestPatternDetection -v

# Run with make command
make test
```

### Local Testing

```bash
# Install dependencies first
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Run tests
pytest test_app_basic.py -v
```

## Test Categories

### 1. TestBasicFunctionality (3/3 tests)

Tests core API endpoint functionality and system health.

**Tests:**
- `test_health_check` - Validates `/health` endpoint returns correct status and version
- `test_compliance_patterns_endpoint` - Validates `/compliance/patterns` returns available patterns
- `test_compliance_config_endpoint` - Validates `/compliance/config` returns current configuration

**Key Validations:**
- API endpoints respond with correct HTTP status codes
- Response data contains required fields
- System health indicators are present

### 2. TestPatternDetection (4/4 tests)

Tests the regex-based pattern detection system directly.

**Tests:**
- `test_email_detection` - Email pattern detection with correct scoring
- `test_ssn_detection` - SSN pattern detection with blocking behavior
- `test_phone_detection` - Phone number pattern detection
- `test_safe_content` - Ensures no false positives on safe content

**Key Validations:**
- Pattern scoring matches expected values
- Blocking thresholds work correctly
- Rule triggering provides descriptive information
- No false positives on benign content

### 3. TestRiskAssessment (3/3 tests)

Tests the `/assess-risk` API endpoint with combined scoring.

**Tests:**
- `test_assess_risk_safe_content` - Safe content returns zero risk score
- `test_assess_risk_email` - Email detection with Presidio + pattern scoring
- `test_assess_risk_ssn` - SSN detection with blocking behavior

**Key Validations:**
- Combined Presidio + pattern scoring works correctly
- API returns detailed entity information
- Blocking decisions match scoring thresholds
- Response includes both pattern and ML detection results

### 4. TestStreamingEndpoint (3/3 tests)

Tests the streaming chat endpoints and validation logic.

**Tests:**
- `test_chat_stream_no_api_key` - API key validation
- `test_chat_stream_validation` - Request validation (empty messages, size limits, parameters)
- `test_legacy_get_endpoint` - Legacy GET endpoint compatibility

**Key Validations:**
- SSE (Server-Sent Events) headers are correct
- Request validation prevents invalid input
- API key handling works properly
- Legacy endpoint maintains compatibility

### 5. TestPresidioIntegration (3/3 tests)

Tests Microsoft Presidio ML-based detection integration.

**Tests:**
- `test_presidio_initialization` - Presidio detector initializes properly
- `test_presidio_analysis_no_entities` - Handles content with no detected entities
- `test_presidio_analysis_with_email` - Detects entities in email-containing text

**Key Validations:**
- Presidio analyzer loads successfully with spaCy models
- ML detection returns appropriate confidence scores
- Entity extraction provides detailed information
- Graceful handling when no entities detected

## Test Data and Scenarios

### Pattern Detection Test Cases

**Email Patterns:**
- `john.doe@example.com` - Standard email format
- `test@example.com` - Simple test case

**SSN Patterns:**
- `123-45-6789` - Standard SSN format (blocks by default)

**Phone Patterns:**
- `(555) 123-4567` - US phone number format

**Safe Content:**
- `"What is the weather today?"` - Benign question
- `"Hello world"` - Simple greeting

### Expected Behavior

**Scoring System:**
- Email: 0.4 (pattern) + 0.9 (Presidio) = 1.3 total → **Blocked** (>1.0)
- SSN: 1.2 (pattern) + Presidio score → **Blocked** (>1.0)  
- Phone: 0.5 (pattern) + potential Presidio → May or may not block
- Safe content: 0.0 total → **Not blocked**

**Response Format:**
```json
{
  "score": 1.3,
  "blocked": true,
  "pattern_score": 0.4,
  "presidio_score": 0.9,
  "triggered_rules": ["email: Pattern detected"],
  "presidio_entities": [
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 12,
      "end": 28,
      "score": 1.0,
      "text": "test@example.com"
    }
  ],
  "compliance_region": null,
  "snippet_hash": "92ecd0f09ce433c3",
  "timestamp": "2025-08-22T22:15:43.981811"
}
```

## Test Environment Setup

### Dependencies

The test suite requires these key dependencies:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting  
- `httpx` - HTTP client for API testing
- `fastapi[testing]` - FastAPI test client
- `unittest.mock` - Mocking for isolated testing

### Docker Environment

When running tests in Docker:
- Presidio models are automatically downloaded and cached
- spaCy `en_core_web_lg` model is pre-installed
- OpenAI API key is configured from environment
- All dependencies are pre-installed and ready

### Configuration

Tests run with standard configuration:
- Risk threshold: 1.0 (default)
- Presidio confidence: 0.6 (default)
- All compliance features enabled
- Test-safe OpenAI API key configured

## Debugging Failed Tests

### Common Issues

**Import Errors:**
```bash
# Fix: Ensure all dependencies installed
pip install -r requirements.txt
```

**Presidio Model Errors:**
```bash
# Fix: Download spaCy model
python -m spacy download en_core_web_lg
```

**API Key Issues:**
```bash
# Fix: Set valid OpenAI API key
export OPENAI_API_KEY=your_key_here
```

**Docker Permission Issues:**
```bash
# Fix: Use sudo with docker commands
sudo docker compose run --rm api pytest test_app_basic.py -v
```

### Test Output Analysis

**Successful Test Run:**
```
======================== 16 passed, 3 warnings in 4.28s ========================
```

**With Verbose Output:**
```
test_app_basic.py::TestBasicFunctionality::test_health_check PASSED      [  6%]
test_app_basic.py::TestPatternDetection::test_email_detection PASSED     [ 25%]
...
```

**Expected Warnings:**
- SpaCy deprecation warnings (safe to ignore)
- Pydantic migration warnings (cosmetic, not functional issues)

## Performance Testing

### Basic Performance Validation

```bash
# Time-based test execution
time sudo docker exec blocking-responses-api pytest test_app_basic.py

# Expected: ~4-6 seconds for full suite
```

### Load Testing (Optional)

```bash
# Simple concurrent test
make perf-test

# Or manual load test
for i in {1..10}; do
  curl -X POST "http://localhost:8000/assess-risk?text=test" &
done
wait
```

## Coverage Analysis

### Running Coverage Reports

```bash
# Generate HTML coverage report
sudo docker compose run --rm api pytest test_app_basic.py --cov=app --cov-report=html

# View coverage summary
sudo docker compose run --rm api pytest test_app_basic.py --cov=app --cov-report=term
```

### Coverage Targets

**Current Coverage:**
- Core pattern detection: 100%
- API endpoints: 100%
- Configuration handling: 100%
- Presidio integration: 100%

**Areas with Limited Coverage:**
- Error handling edge cases
- Network failure scenarios
- Resource exhaustion conditions

## Best Practices

### Writing New Tests

1. **Follow existing patterns** - Use the same test structure and naming
2. **Test real behavior** - Validate actual API responses, not mocked behavior
3. **Use descriptive assertions** - Make test failures easy to understand
4. **Test edge cases** - Include boundary conditions and error scenarios

### Test Maintenance

1. **Update tests with code changes** - Keep tests aligned with implementation
2. **Validate test assumptions** - Ensure tests match actual system behavior
3. **Monitor test performance** - Keep test execution time reasonable
4. **Document test changes** - Update this guide when adding new test categories

### Integration with CI/CD

```bash
# Example CI pipeline test command
docker-compose run --rm api pytest test_app_basic.py --cov=app --cov-report=xml
```

The test suite is designed to be:
- **Fast** - Complete execution in under 10 seconds
- **Reliable** - Consistent results across environments  
- **Comprehensive** - Covers all critical functionality
- **Maintainable** - Clear structure and documentation