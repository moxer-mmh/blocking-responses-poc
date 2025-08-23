# 🧪 Complete Testing Guide - Blocking Responses API

This comprehensive guide covers all testing scenarios for the regulated compliance system, from basic functionality to advanced compliance scenarios.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Testing Environments](#testing-environments)
4. [API Testing](#api-testing)
5. [Compliance Testing](#compliance-testing)
6. [Frontend Testing](#frontend-testing)
7. [Integration Testing](#integration-testing)
8. [Performance Testing](#performance-testing)
9. [Troubleshooting](#troubleshooting)

## 🛠 Prerequisites

### Required Software
- **Docker** (v20.0+) and **Docker Compose** (v2.0+)
- **curl** or **Postman** for API testing
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **OpenAI API Key** with sufficient credits

### System Requirements
- **Memory**: Minimum 4GB RAM (Presidio ML models)
- **Storage**: 2GB free space (Docker images)
- **Network**: Internet access for OpenAI API calls

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd blocking-responses-poc

# Create environment file
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4o-mini
RISK_THRESHOLD=1.0
LOG_LEVEL=INFO
EOF

# Start all services
docker-compose up -d --build

# Wait for services to be ready (60-90 seconds)
docker-compose logs -f
```

### 2. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-01-XX...",
  "uptime_seconds": XX,
  "presidio_loaded": true,
  "tiktoken_available": true,
  "openai_configured": true
}

# Check frontend
curl http://localhost/

# Should return HTML dashboard
```

## 🏢 Testing Environments

### Development Environment
```bash
# Run API only for development
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Frontend development
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### Production Environment
```bash
# Full Docker deployment
docker-compose up -d --build

# Access:
# - API: http://localhost:8000
# - Dashboard: http://localhost
```

### Testing with Custom Configuration
```bash
# Custom environment variables
OPENAI_API_KEY=sk-... \
RISK_THRESHOLD=0.5 \
ENABLE_JUDGE=false \
docker-compose up -d
```

## 🔌 API Testing

### Core Endpoints

#### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```

#### 2. Configuration
```bash
curl -X GET http://localhost:8000/config
```

#### 3. Risk Assessment
```bash
# Basic risk assessment
curl -X POST "http://localhost:8000/assess-risk?text=Hello world"

# With sensitive data
curl -X POST "http://localhost:8000/assess-risk?text=My SSN is 123-45-6789"

# With region specification
curl -X POST "http://localhost:8000/assess-risk?text=Patient ID: 12345&region=HIPAA"
```

#### 4. Streaming Chat (SSE)
```bash
# Simple streaming test
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/chat/stream \
  -d '{"message": "Tell me about data privacy"}'

# With API key override
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/chat/stream \
  -d '{
    "message": "Generate a medical report",
    "api_key": "your_openai_key",
    "risk_threshold": 0.8,
    "region": "HIPAA"
  }'
```

#### 5. Audit Logs
```bash
# Get recent audit logs
curl -X GET "http://localhost:8000/audit/logs?limit=10"

# Filter by event type
curl -X GET "http://localhost:8000/audit/logs?event_type=compliance_check&limit=5"
```

### Advanced API Testing

#### Browser Testing with EventSource
```javascript
// Open browser console on http://localhost:8000/docs
const eventSource = new EventSource('http://localhost:8000/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello' })
});

eventSource.onmessage = function(event) {
  console.log('Received:', event.data);
};

eventSource.onerror = function(event) {
  console.error('Error:', event);
};
```

## 🛡️ Compliance Testing

### PII Detection Tests

#### Email Detection
```bash
curl -X POST "http://localhost:8000/assess-risk?text=Contact me at john.doe@company.com"
# Expected: High risk score, email entity detected
```

#### SSN Detection
```bash
curl -X POST "http://localhost:8000/assess-risk?text=My social security number is 123-45-6789"
# Expected: Very high risk score, SSN entity detected
```

#### Credit Card Detection
```bash
curl -X POST "http://localhost:8000/assess-risk?text=My card number is 4111-1111-1111-1111"
# Expected: Very high risk score, credit card detected
```

#### Phone Number Detection
```bash
curl -X POST "http://localhost:8000/assess-risk?text=Call me at (555) 123-4567"
# Expected: Medium risk score, phone entity detected
```

### PHI (HIPAA) Testing

```bash
# Medical record number
curl -X POST "http://localhost:8000/assess-risk?text=Patient MRN: 123456789&region=HIPAA"

# Medical diagnosis
curl -X POST "http://localhost:8000/assess-risk?text=Diagnosed with diabetes type 2&region=HIPAA"

# Prescription information
curl -X POST "http://localhost:8000/assess-risk?text=Prescribed metformin 500mg&region=HIPAA"
```

### PCI Testing

```bash
# Credit card with context
curl -X POST "http://localhost:8000/assess-risk?text=Process payment for card 4111111111111111&region=PCI"

# Banking information
curl -X POST "http://localhost:8000/assess-risk?text=Account number: 123456789, routing: 987654321&region=PCI"
```

### Regional Compliance Testing

```bash
# EU GDPR
curl -X POST "http://localhost:8000/assess-risk?text=Personal data: john@example.com&region=EU"

# California CCPA
curl -X POST "http://localhost:8000/assess-risk?text=User email: jane@company.com&region=CCPA"

# Healthcare HIPAA
curl -X POST "http://localhost:8000/assess-risk?text=Patient diagnosed with condition&region=HIPAA"
```

### Streaming Compliance Tests

```bash
# Test real-time blocking
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/chat/stream \
  -d '{
    "message": "Generate a fake SSN for testing",
    "risk_threshold": 0.5
  }'
# Expected: Content should be blocked or rewritten
```

## 🎨 Frontend Testing

### Dashboard Access
1. Open http://localhost in browser
2. Navigate through all sections:
   - **Dashboard**: Overview metrics
   - **Stream Monitor**: Live compliance monitoring
   - **Audit Logs**: Historical compliance data
   - **Test Suite**: Interactive testing tools

### Settings Modal Testing
1. Click settings icon in header
2. Test API key configuration:
   - Enter OpenAI API key
   - Verify it's saved to localStorage
   - Test with different API key
3. Test theme selection
4. Verify security status display

### Notifications Testing
1. Click notification bell icon
2. Verify notifications are displayed
3. Test "Mark all as read" functionality
4. Verify badge count updates

### Live Stream Testing
1. Go to **Stream Monitor** page
2. Enter test messages with PII:
   - "My email is test@example.com"
   - "SSN: 123-45-6789"
   - "Credit card: 4111-1111-1111-1111"
3. Verify real-time compliance detection
4. Check audit log entries appear

### Charts and Metrics
1. Go to **Dashboard** page
2. Verify metrics charts display:
   - Request activity over time
   - Compliance breakdown
   - Risk score distribution
3. Test data refresh functionality

## 🔄 Integration Testing

### Full Workflow Test
```bash
#!/bin/bash
# Complete integration test script

echo "1. Testing health endpoint..."
curl -f http://localhost:8000/health || exit 1

echo "2. Testing configuration..."
curl -f http://localhost:8000/config || exit 1

echo "3. Testing risk assessment..."
RESULT=$(curl -s -X POST "http://localhost:8000/assess-risk?text=test@example.com")
echo $RESULT | grep -q "risk_score" || exit 1

echo "4. Testing streaming..."
timeout 10s curl -N -H "Accept: text/event-stream" \
  -X POST http://localhost:8000/chat/stream \
  -d '{"message":"Hello"}' | head -5

echo "5. Testing audit logs..."
curl -f "http://localhost:8000/audit/logs?limit=1" || exit 1

echo "6. Testing frontend..."
curl -f http://localhost/ | grep -q "Compliance Dashboard" || exit 1

echo "✅ All integration tests passed!"
```

### Docker Health Checks
```bash
# Check container health
docker-compose ps

# Check individual container logs
docker-compose logs api
docker-compose logs frontend

# Test container communication
docker-compose exec api curl http://frontend/health
```

## ⚡ Performance Testing

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install httpie  # macOS

# Basic load test
ab -n 100 -c 10 http://localhost:8000/health

# Streaming load test
for i in {1..10}; do
  curl -N -H "Accept: text/event-stream" \
    -X POST http://localhost:8000/chat/stream \
    -d '{"message":"Test '$i'"}' &
done
wait
```

### Memory and CPU Monitoring
```bash
# Monitor Docker containers
docker stats

# Monitor specific container
docker stats blocking-responses-api

# Check Presidio model memory usage
docker exec blocking-responses-api ps aux | grep python
```

### Database Performance
```bash
# Check audit log performance
time curl -s "http://localhost:8000/audit/logs?limit=1000" > /dev/null

# Check metrics performance
time curl -s "http://localhost:8000/metrics/summary" > /dev/null
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker daemon
docker info

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :80

# Clear Docker cache
docker system prune -a
```

#### 2. OpenAI API Issues
```bash
# Test API key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check environment variables
docker-compose exec api env | grep OPENAI
```

#### 3. Presidio Loading Issues
```bash
# Check Presidio installation
docker-compose exec api python -c "from presidio_analyzer import AnalyzerEngine; print('OK')"

# Check spaCy model
docker-compose exec api python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('OK')"
```

#### 4. Frontend Issues
```bash
# Check nginx status
docker-compose exec frontend nginx -t

# Check build files
docker-compose exec frontend ls -la /usr/share/nginx/html/

# Check API connectivity from frontend
docker-compose exec frontend curl http://api:8000/health
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set debug environment
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart api

# View debug logs
docker-compose logs -f api | grep DEBUG
```

#### API Debug Endpoints
```bash
# Get detailed system info
curl http://localhost:8000/debug/info

# Get active patterns
curl http://localhost:8000/debug/patterns

# Test Presidio directly
curl -X POST "http://localhost:8000/debug/presidio" \
  -H "Content-Type: application/json" \
  -d '{"text": "test@example.com"}'
```

### Performance Tuning

#### Memory Optimization
```bash
# Reduce Presidio model size
echo "PRESIDIO_MODEL=en_core_web_sm" >> .env
docker-compose restart api
```

#### CPU Optimization
```bash
# Limit container resources
docker-compose exec api docker update --cpus="2" --memory="4g" blocking-responses-api
```

## 📝 Test Results Documentation

### Creating Test Reports
```bash
# Generate comprehensive test report
./run_all_tests.sh > test_results_$(date +%Y%m%d_%H%M%S).log 2>&1

# Performance baseline
curl -w "@curl-format.txt" -s http://localhost:8000/health
```

### Compliance Test Matrix

| Test Case | Input | Expected Result | Status |
|-----------|-------|----------------|---------|
| Email PII | "Contact: user@domain.com" | Risk Score > 0.4, Email entity | ✅ |
| SSN Detection | "SSN: 123-45-6789" | Risk Score > 1.0, SSN entity | ✅ |
| Credit Card | "Card: 4111-1111-1111-1111" | Risk Score > 1.5, CC entity | ✅ |
| HIPAA PHI | "Patient MRN: 12345" | Risk Score > 0.8, Medical entity | ✅ |
| Safe Content | "Hello world" | Risk Score < 0.1, No entities | ✅ |

This comprehensive testing guide ensures you can thoroughly validate all aspects of the compliance system, from basic functionality to advanced regulatory scenarios.
