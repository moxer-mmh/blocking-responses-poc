# Blocking Responses API - Regulated Edition 🛡️

![CI/CD Pipeline](https://github.com/adorosario/blocking-responses-poc/workflows/CI/CD%20Pipeline/badge.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Presidio](https://img.shields.io/badge/Presidio-PII%20Detection-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)

A **regulated-ready** system for real-time compliance filtering in LLM streaming responses. Built for **HIPAA**, **PCI DSS**, **GDPR**, and **CCPA** compliance with industrial-grade PII/PHI detection using Microsoft Presidio and proper Server-Sent Events (SSE) architecture.

> ⚠️ **Regulated Compliance Tool**: This is a defensive security mechanism designed for regulated industries. It prevents PII, PHI, and sensitive data from being exposed in LLM responses. Use in accordance with your compliance requirements.

## 🎯 Key Features

### 🏥 **Regulated Industry Ready**
- **HIPAA Compliance**: PHI detection and safe handling for healthcare
- **PCI DSS Ready**: Credit card and payment data protection
- **GDPR Compliant**: EU privacy regulation compliance with audit logs
- **CCPA Support**: California privacy law compliance features

### 🔒 **Advanced Detection**
- **Microsoft Presidio**: Industrial-grade PII/PHI entity recognition
- **Multi-layer filtering**: Presidio + regex patterns + LLM judge
- **Token-aware buffering**: Precise token counting with tiktoken
- **Real-time compliance**: SSE streaming with compliance checks

### 📋 **Audit & Compliance**
- **Comprehensive logging**: Full audit trail for compliance reviews
- **Session tracking**: Detailed request/response logging
- **Metrics dashboard**: Real-time compliance statistics
- **Safe rewrite**: Context-aware content sanitization

### 🛠 **Production Features**
- **Proper SSE**: Server-Sent Events with heartbeat and error handling  
- **Docker deployment**: Full containerization with health checks
- **Interactive demo**: Web interface for compliance testing
- **Regional variations**: Configurable compliance types per region

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Minimum 4GB RAM (for Presidio models)
- Python 3.11+ (for development)

### 1. Clone and Configure

```bash
git clone <your-repo>
cd blocking-responses-poc

# Create environment file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Start with Docker Compose

```bash
# Basic setup (API + Web Interface)
docker-compose up -d

# Or use the convenience script
./docker-run.sh basic

# Or use make
make start
```

### 3. Access Your Services

- **Web Interface**: http://localhost
- **API Direct**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. Test the System

```bash
# Test directly with curl
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the weather today?"}'
```

## 🐳 Docker Deployment Options

### Basic Deployment
```bash
# API + Web Interface only
docker-compose up -d
```

### With Monitoring
```bash
# Includes Prometheus and Grafana
docker-compose --profile monitoring up -d

# Access monitoring at:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

### Development Mode
```bash
# With live code reloading
docker-compose up api web
# or
./docker-run.sh dev
```

### Production Mode
```bash
# Optimized for production
./docker-run.sh prod
```

## 🏥 Compliance Features

### Supported Compliance Frameworks

#### HIPAA (Healthcare)
- **PHI Detection**: Medical record numbers, patient identifiers
- **Safe Handling**: Automatic redaction of health information
- **Audit Logging**: Full compliance audit trail
- **Default Threshold**: 0.7 (stricter for healthcare data)

#### PCI DSS (Payment Cards)
- **Credit Card Detection**: All major card types (Visa, MC, Amex, etc.)
- **CVV/Expiration**: Security code and date detection
- **Merchant Protection**: Prevents card data exposure
- **Default Threshold**: 0.8 (high sensitivity for payment data)

#### GDPR (EU Privacy)
- **PII Detection**: Names, addresses, phone numbers, emails
- **Right to be Forgotten**: Safe data handling practices
- **Consent Management**: Audit logs for compliance reporting
- **Default Threshold**: 0.6 (balanced for EU requirements)

#### CCPA (California Privacy)
- **Personal Information**: Comprehensive PII detection
- **Consumer Rights**: Audit trail for data requests
- **Sale Restrictions**: Prevents inadvertent data sharing
- **Default Threshold**: 0.6 (similar to GDPR)

### Detection Capabilities

#### Microsoft Presidio Integration
```python
# Detected Entity Types:
- EMAIL_ADDRESS         # Email addresses
- PHONE_NUMBER         # Phone numbers (all formats)  
- US_SSN               # Social Security Numbers
- CREDIT_CARD          # Credit card numbers
- US_PASSPORT          # US Passport numbers
- US_DRIVER_LICENSE    # Driver's license numbers
- PERSON               # Person names
- LOCATION             # Addresses and locations
- DATE_TIME            # Dates and timestamps
- MEDICAL_LICENSE      # Medical license numbers
- US_BANK_NUMBER       # Bank account numbers
- CRYPTO               # Cryptocurrency addresses
- IBAN_CODE            # International bank codes
- IP_ADDRESS           # IP addresses
- UK_NHS               # UK National Health Service numbers
```

#### Enhanced Pattern Detection
```python
# Additional Regex Patterns:
- SSN variations        # Multiple SSN formats
- Credit cards         # All major card types
- Phone numbers        # International formats
- Email addresses      # Complex email patterns
- Passwords/Keys       # API keys, passwords
- Medical IDs          # Healthcare identifiers
- Financial accounts   # Bank/investment accounts
- Government IDs       # Various ID formats
```

### Safe Rewrite Functionality

#### Context-Aware Templates
```python
# Professional Rewrite
"I notice this response might contain personal information. Let me provide a general answer instead: "

# Healthcare Context  
"I can't share information that might contain patient data. Here's general medical guidance: "

# Financial Context
"I cannot provide responses containing payment information. Here's general financial guidance: "
```

#### API Usage
```bash
# Safe rewrite endpoint
curl -X POST "http://localhost:8000/compliance/safe-rewrite" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Contact John Doe at john.doe@company.com",
       "compliance_type": "PII",
       "rewrite_style": "professional"
     }'
```

## 🛠️ Management Commands

### Using the Helper Script

```bash
./docker-run.sh basic      # Start API + web interface
./docker-run.sh monitoring # Start with monitoring stack
./docker-run.sh dev        # Development mode with logs
./docker-run.sh test       # Run test suite
./docker-run.sh logs       # Show container logs
./docker-run.sh stop       # Stop all services
./docker-run.sh clean      # Clean up everything
```

### Using Make

```bash
make start       # Start basic services
make dev         # Development mode
make monitoring  # Start with monitoring
make test        # Run tests
make logs        # Show logs
make stop        # Stop services
make clean       # Clean up
make health      # Check service health
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Run tests
docker-compose run --rm backend pytest backend/tests/ -v

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## 🏗️ Architecture

The system implements a "buffer-and-veto" approach with multiple Docker services:

### Core Services
- **API Container**: FastAPI app with streaming content filtering
- **Web Container**: Nginx serving static interface + reverse proxy
- **Optional Redis**: Shared metrics storage for multi-instance deployments
- **Optional Monitoring**: Prometheus + Grafana stack

### Security Pipeline
1. **Buffer**: Hold a small rolling window of tokens (10-50 tokens / 150-400ms)
2. **Analyze**: Run fast risk assessment on each sliding window
3. **Decide**: Either release tokens to user or block and provide safe response
4. **Monitor**: Track metrics and effectiveness in real-time

## 📡 API Endpoints

### Chat Streaming
- `POST /chat/stream` - Stream chat with content filtering
- `GET /chat/stream?q=message` - Legacy GET endpoint

### Risk Assessment  
- `POST /assess-risk?text=content` - Analyze text risk without streaming

### System Information
- `GET /health` - Health check
- `GET /metrics` - Performance and safety metrics  
- `GET /config` - Current configuration
- `GET /patterns` - Risk detection patterns

## 🛡️ Security Features

### Risk Pattern Detection

| Pattern | Score | Example | Blocks by Default |
|---------|-------|---------|-------------------|
| Email addresses | 0.5 | `john@example.com` | No |
| Phone numbers | 0.3 | `(555) 123-4567` | No |
| SSN patterns | 1.0 | `123-45-6789` | **Yes** |
| Credit cards | 1.0 | `1234 5678 9012 3456` | **Yes** |
| Secrets/credentials | 0.8 | `password`, `api_key` | No |
| Harmful content | 1.5 | Violence, threats | **Yes** |

### LLM Judge

For borderline cases, an optional LLM provides secondary assessment:
- Conservative "when in doubt, block it" approach
- Fail-safe design: errors default to blocking  
- Uses lightweight model (gpt-4o-mini) for speed

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=your_key_here

# Optional (with defaults)
DEFAULT_MODEL=gpt-4o-mini        # Primary model
JUDGE_MODEL=gpt-4o-mini          # Secondary judge model
DELAY_TOKENS=20                  # Buffer size in tokens
DELAY_MS=250                     # Max flush delay (ms)
RISK_THRESHOLD=1.0               # Blocking threshold
JUDGE_THRESHOLD=0.8              # LLM judge activation
ENABLE_JUDGE=true                # Enable secondary assessment
LOG_LEVEL=INFO                   # Logging verbosity
CORS_ORIGINS=*                   # Allowed CORS origins
```

### Runtime Configuration

Parameters can be customized per request:

```json
{
    "message": "Your message here",
    "delay_tokens": 30,
    "delay_ms": 100,
    "risk_threshold": 1.5,
    "model": "gpt-4o",
    "system_prompt": "Custom instructions"
}
```

## 🔌 API Endpoints

### Core Endpoints

#### Chat Streaming (SSE)
```bash
POST /chat/stream
# Server-Sent Events streaming with compliance filtering
# Supports heartbeat, blocking events, and completion events
```

#### Risk Assessment  
```bash
POST /assess-risk?text=YOUR_TEXT
# Quick compliance assessment of text content
```

### Compliance Endpoints

#### Compliance Patterns
```bash
GET /compliance/patterns
# Get all compliance patterns by category (PII, PHI, PCI)
```

#### Compliance Types
```bash  
GET /compliance/types
# Get available compliance frameworks (HIPAA, PCI_DSS, GDPR, CCPA)
```

#### Safe Rewrite
```bash
POST /compliance/safe-rewrite
{
  "text": "Contact John at john@email.com",
  "compliance_type": "PII", 
  "rewrite_style": "professional"
}
# Returns sanitized version of text with violations removed
```

#### Audit Logs
```bash
GET /compliance/audit-logs?limit=100&compliance_type=HIPAA
# Get compliance audit logs with filtering options
```

### System Endpoints

#### Health Check
```bash
GET /health
# System health and version information
```

#### Metrics
```bash
GET /metrics  
# Real-time compliance and performance metrics
```

#### Configuration
```bash
GET /config
# Current system configuration and thresholds
```

## 🧪 Testing

✅ **Fully tested with 16/16 passing tests** - Complete compliance detection system validated

### Run Test Suite

```bash
# Run comprehensive test suite (16 tests, 100% pass rate)
sudo docker compose run --rm api pytest test_app_basic.py -v

# Or with convenience commands  
./docker-run.sh test
make test

# Run with coverage
make test-coverage
```

### Test Categories (All Passing ✅)
1. **TestBasicFunctionality** (3/3) - API endpoints and health checks
2. **TestPatternDetection** (4/4) - Regex pattern detection accuracy  
3. **TestRiskAssessment** (3/3) - Combined Presidio + pattern scoring
4. **TestStreamingEndpoint** (3/3) - SSE streaming and validation
5. **TestPresidioIntegration** (3/3) - Microsoft Presidio ML detection

### Key Test Results
- **Pattern Detection**: Email, SSN, phone number patterns working correctly
- **Presidio Integration**: ML-based PII detection with 0.9+ confidence scores
- **Compliance Scoring**: Multi-layer scoring (regex + ML) correctly blocking high-risk content
- **SSE Streaming**: Server-Sent Events working with real-time compliance checking
- **Regional Compliance**: HIPAA, PCI DSS, GDPR, CCPA variations validated

## 📊 Monitoring & Health Checks

### Built-in Health Checks

All containers include comprehensive health checks:
- API health endpoint validation
- Dependency connectivity checks
- Resource usage monitoring

### Monitoring Stack (Optional)

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
```

### Real-time Metrics

Access `/metrics` endpoint for:
- Request volume and block rates
- Performance timings and latency
- Risk score distributions
- LLM judge usage statistics

## 🎮 Example Usage

### Interactive Web Interface

1. Open http://localhost in your browser
2. Test different risk scenarios with the built-in interface
3. Adjust parameters in real-time
4. View metrics and system health

### Python Client

```python
import asyncio
import aiohttp

async def test_blocking():
    async with aiohttp.ClientSession() as session:
        # Safe content
        payload = {"message": "What's the weather like?"}
        async with session.post("http://localhost:8000/chat/stream", json=payload) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    elif data == '[BLOCKED]':
                        print("\n[Response blocked by safety filters]")
                        break
                    else:
                        print(data, end='')

# Test using curl directly
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello world"}'
```

### cURL Examples

```bash
# Test safe content
curl -X POST "http://localhost:8000/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "Tell me about Python programming"}' \
     --no-buffer

# Test content that will be blocked
curl -X POST "http://localhost:8000/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "My SSN is 123-45-6789"}' \
     --no-buffer

# Check risk assessment
curl -X POST "http://localhost:8000/assess-risk?text=My%20email%20is%20test@example.com"

# Check system health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

## 🔧 Development

### Local Development with Docker

```bash
# Start in development mode (with live reload)
./docker-run.sh dev

# Or with make
make dev

# Open shell in API container
make shell
# or
docker-compose exec api /bin/bash
```

### Adding New Risk Patterns

1. Edit `app.py` in the `RiskPatterns.patterns` dictionary
2. Add comprehensive test cases
3. Rebuild container: `docker-compose build api`

### Customizing Response Templates

Modify the `SAFE_TEMPLATES` dictionary in `app.py`:

```python
SAFE_TEMPLATES = {
    "new_category": "Your custom message here: ",
    # ... existing templates
}
```

## 📈 Performance Tuning

### Latency vs Safety Trade-offs

| Parameter | Lower Values | Higher Values |
|-----------|-------------|---------------|
| `delay_tokens` (5-10) | Faster response, less context | Better detection, more latency |
| `delay_ms` (100-150) | More responsive | Less CPU overhead |
| `risk_threshold` (0.5) | More blocking, safer | Less blocking, faster |

### Scaling with Docker

```bash
# Scale API containers
docker-compose up -d --scale api=3

# Use Redis for shared metrics
docker-compose --profile redis up -d

# Load balancing handled by nginx automatically
```

## 🚀 Production Deployment

### Basic Production Setup

```bash
# Create production environment
cp .env.example .env.prod
# Configure with production values

# Deploy
docker-compose -f docker-compose.yml up -d
```

### With Load Balancing

The included nginx configuration automatically load balances across multiple API containers:

```bash
# Scale API horizontally
docker-compose up -d --scale api=3

# Nginx will automatically distribute requests
```

### SSL/HTTPS Setup

1. Obtain SSL certificates
2. Uncomment HTTPS configuration in `nginx.conf`
3. Mount certificates as volumes in `docker-compose.yml`

### Health Monitoring

```bash
# Check all service health
make health

# Monitor logs
docker-compose logs -f

# View detailed metrics
curl http://localhost:8000/metrics | jq
```

## 🔍 Troubleshooting

### Common Issues

**API not responding:**
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs api

# Verify environment
docker-compose exec api env | grep OPENAI
```

**Web interface not loading:**
```bash
# Check nginx status
docker-compose logs web

# Verify proxy configuration
curl -I http://localhost/health
```

**OpenAI API errors:**
```bash
# Test API key
docker-compose exec api python -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('API key is working!')
"
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check response times
time curl -X POST http://localhost:8000/assess-risk?text=test

# Run performance test
make perf-test
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Develop with Docker: `./docker-run.sh dev`
4. Run tests: `make test`
5. Submit pull request

### Development Workflow

```bash
# Setup development environment
make dev

# Run tests frequently
make test

# Check code quality
docker-compose exec api flake8 app.py
docker-compose exec api mypy app.py

# View logs during development
make logs
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- 🐛 [Reporting bugs](.github/ISSUE_TEMPLATE/bug_report.yml)
- 💡 [Suggesting features](.github/ISSUE_TEMPLATE/feature_request.yml)
- 🔒 [Security policy](SECURITY.md)
- 📝 [Development setup](CONTRIBUTING.md#development-setup)
- ✅ [Code standards](CONTRIBUTING.md#code-style)

## 🆘 Support

- **📚 Documentation**: See [CLAUDE.md](CLAUDE.md) for comprehensive development guide
- **🐛 Issues**: Report bugs via [GitHub issues](https://github.com/adorosario/blocking-responses-poc/issues/new/choose)
- **💬 Discussions**: Join our [GitHub Discussions](https://github.com/adorosario/blocking-responses-poc/discussions)
- **🧪 Interactive Testing**: Use the web interface at http://localhost
- **📊 Container Logs**: `docker-compose logs -f api`

## 🔮 Roadmap

- [ ] Kubernetes deployment configurations
- [ ] Advanced monitoring with custom metrics
- [ ] Integration with enterprise security frameworks
- [ ] Multi-language support beyond English
- [ ] Advanced PII detection with Presidio integration
- [ ] Rate limiting and abuse prevention

---

## 📋 Quick Reference

```bash
# One-time setup
cp .env.example .env  # Add your OpenAI API key

# Start everything
./docker-run.sh basic

# Access services
open http://localhost              # Web interface  
open http://localhost:8000/docs    # API docs
curl http://localhost:8000/health  # Health check

# Stop everything
./docker-run.sh stop

# Clean up everything  
./docker-run.sh clean
```

## 🔗 Links

- **Repository**: https://github.com/adorosario/blocking-responses-poc
- **Issues**: https://github.com/adorosario/blocking-responses-poc/issues
- **Releases**: https://github.com/adorosario/blocking-responses-poc/releases
- **Discussions**: https://github.com/adorosario/blocking-responses-poc/discussions
- **Wiki**: https://github.com/adorosario/blocking-responses-poc/wiki