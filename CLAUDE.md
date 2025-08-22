# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a complete FastAPI-based system for implementing "blocking responses" - a security mechanism that monitors LLM streaming responses in real-time and can block or redirect potentially unsafe content before it reaches the user. It includes a full API, comprehensive test suite, example clients, and deployment configurations.

## Architecture

### Core Components

1. **Risk Pattern Engine** (`RiskPatterns`): Configurable regex-based detection for PII, credentials, and harmful content
2. **LLM Judge** (`LLMJudge`): Secondary AI-based content safety assessment for complex cases
3. **Streaming Filter** (`guarded_stream()`): Buffer-and-veto mechanism with configurable delays and thresholds
4. **Metrics System** (`Metrics`): Real-time tracking of blocking rates, performance, and safety statistics
5. **Configuration Management** (`Settings`): Environment-based configuration with validation

### API Endpoints

- `POST /chat/stream`: Main streaming endpoint with content filtering
- `GET /chat/stream`: Legacy endpoint for backwards compatibility
- `POST /assess-risk`: Risk assessment without streaming
- `GET /health`: Health check endpoint
- `GET /metrics`: System performance and safety metrics
- `GET /config`: Current configuration settings
- `GET /patterns`: Risk detection patterns and rules

### Safety Mechanisms

- **Multi-layer filtering**: Fast regex patterns + optional LLM judge
- **Configurable thresholds**: Adjustable risk scoring and blocking levels
- **Safe response templates**: Context-aware replacement messages
- **Real-time metrics**: Monitor blocking effectiveness and false positive rates
- **Fail-safe design**: Defaults to blocking on errors or uncertainty

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running the Server
```bash
# Development mode
uvicorn app:app --reload

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Run all tests
pytest test_app.py -v

# Run specific test categories
pytest test_app.py::TestRiskPatterns -v
pytest test_app.py::TestChatStreaming -v

# Run with coverage
pytest test_app.py --cov=app --cov-report=html
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access API at http://localhost:8000
# Access web interface at http://localhost:80
```

### Example Client
```bash
# Run demos
python example_client.py

# Interactive mode
python example_client.py interactive
```

## Configuration

### Environment Variables (.env)
- `OPENAI_API_KEY`: Required for LLM functionality
- `DEFAULT_MODEL`: Primary LLM model (default: gpt-4o-mini)
- `JUDGE_MODEL`: Secondary safety judge model (default: gpt-4o-mini)
- `DELAY_TOKENS`: Buffer size in tokens (default: 20)
- `DELAY_MS`: Maximum flush delay in milliseconds (default: 250)
- `RISK_THRESHOLD`: Blocking threshold (default: 1.0)
- `JUDGE_THRESHOLD`: LLM judge activation threshold (default: 0.8)
- `ENABLE_JUDGE`: Enable/disable LLM judge (default: true)
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `CORS_ORIGINS`: Allowed CORS origins (default: *)

### Risk Patterns and Scoring
- **Email addresses**: 0.5 points
- **Phone numbers**: 0.3 points  
- **SSN patterns**: 1.0 points (blocks by default)
- **Credit card patterns**: 1.0 points (blocks by default)
- **Secrets/credentials**: 0.8 points
- **Harmful content**: 1.5 points (blocks by default)

Scores are cumulative - multiple patterns in a response add up.

## Testing Strategy

### Test Categories
1. **Risk Pattern Tests**: Verify detection accuracy for each pattern type
2. **LLM Judge Tests**: Mock-based testing of secondary safety assessment
3. **API Endpoint Tests**: Comprehensive coverage of all endpoints
4. **Streaming Tests**: End-to-end streaming with blocking scenarios
5. **Configuration Tests**: Parameter validation and customization
6. **Error Handling Tests**: Graceful handling of failures and edge cases
7. **Metrics Tests**: Tracking accuracy and performance monitoring

### Test Data Patterns
- Safe content examples
- Individual risk pattern triggers
- Multi-pattern combinations
- Edge cases and boundary conditions
- Error scenarios and malformed input

## Performance Considerations

### Latency Optimization
- Fast regex patterns execute in microseconds
- LLM judge only called for borderline cases (> judge_threshold)
- Configurable buffer sizes balance safety vs. responsiveness
- Time-based flushing prevents indefinite delays

### Scaling Considerations
- Stateless design supports horizontal scaling
- Metrics stored in memory (consider Redis for multi-instance)
- LLM judge calls are the primary bottleneck
- Monitor block rates to tune thresholds

## Security Implementation

### Defense in Depth
1. **Fast filters**: Catch obvious patterns immediately
2. **LLM judge**: Handle nuanced cases and reduce false positives
3. **Configurable thresholds**: Tune sensitivity vs. usability
4. **Safe templates**: Provide helpful responses instead of errors
5. **Audit logging**: Track what's blocked and why

### Privacy Protection
- Text snippets in logs are truncated to 100 characters
- Risk assessments don't store full content
- Metrics are aggregated without sensitive details
- Client disconnection handled to prevent data leaks

## Deployment Options

### Local Development
- Direct Python execution with uvicorn
- Automatic reloading for development
- Environment-based configuration

### Docker Container
- Multi-stage build for optimization
- Non-root user for security
- Health checks and restart policies
- Volume mounts for configuration

### Production Deployment
- NGINX reverse proxy for load balancing
- Environment variable configuration
- Centralized logging and monitoring
- SSL termination and security headers

## Monitoring and Observability

### Key Metrics
- **Total requests**: Volume tracking
- **Block rate**: Safety effectiveness
- **Judge calls**: Secondary assessment usage
- **Average delay**: Performance impact
- **Risk score distribution**: Pattern detection frequency

### Health Monitoring
- `/health` endpoint for load balancer checks
- Application startup validation
- Dependency health (OpenAI API connectivity)
- Resource usage tracking

## Common Development Tasks

### Adding New Risk Patterns
1. Add pattern to `RiskPatterns.patterns` dictionary
2. Include regex, score, and description
3. Add test cases in `TestRiskPatterns`
4. Update documentation

### Modifying Safety Thresholds
1. Update default values in `Settings` class
2. Test with various content types
3. Monitor metrics for effectiveness
4. Document threshold rationale

### Extending LLM Judge
1. Modify system prompt in `LLMJudge.__init__`
2. Adjust response parsing logic
3. Add comprehensive test coverage
4. Monitor performance impact

### Custom Response Templates
1. Add templates to `SAFE_TEMPLATES` dictionary
2. Update `get_safe_template()` logic
3. Test with various blocking scenarios
4. Ensure user-friendly messaging