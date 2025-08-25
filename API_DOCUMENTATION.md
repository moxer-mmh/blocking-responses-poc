# 🔌 API Documentation - Blocking Responses API

## 📋 Overview

The Blocking Responses API provides real-time compliance filtering for AI applications, with support for PII/PHI detection, streaming responses, and comprehensive audit logging.

**Base URL**: `http://localhost:8000`
**Web Interface**: `http://localhost:3000`

**Content-Type**: `application/json`

**Authentication**: Optional OpenAI API key via request body or environment variable

## 🏥 Health & Configuration

### GET /health

System health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "uptime_seconds": 3600,
  "presidio_loaded": true,
  "tiktoken_available": true,
  "openai_configured": true
}
```

### GET /config

Get current system configuration.

**Response**:
```json
{
  "default_model": "gpt-4o-mini",
  "delay_ms": 250,
  "delay_tokens": 20,
  "risk_threshold": 1.0,
  "cors_origins": ["*"]
}
```

## 🔍 Risk Assessment

### POST /assess-risk

Assess compliance risk for given text.

**Parameters**:
- `text` (required): Text to analyze
- `region` (optional): Compliance region (US, EU, HIPAA, PCI)

**Example Request**:
```bash
curl -X POST "http://localhost:8000/assess-risk?text=My email is user@domain.com&region=HIPAA"
```

**Response**:
```json
{
  "risk_score": 0.4,
  "blocked": false,
  "triggered_rules": ["email"],
  "presidio_entities": [
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 12,
      "end": 28,
      "score": 0.85,
      "text": "user@domain.com"
    }
  ],
  "pattern_score": 0.4,
  "compliance_region": "HIPAA",
  "processing_time_ms": 45
}
```

## 💬 Streaming Chat

### POST /chat/stream

Stream AI responses with real-time compliance checking.

**Content-Type**: `application/json`

**Accept**: `text/event-stream`

**Request Body**:
```json
{
  "message": "Tell me about data privacy",
  "model": "gpt-4o-mini",
  "api_key": "sk-...",
  "delay_tokens": 20,
  "delay_ms": 250,
  "risk_threshold": 1.0,
  "enable_safe_rewrite": true,
  "region": "HIPAA"
}
```

**Response Stream**:
```
data: {"chunk": "Data", "risk_score": 0.0, "entities": [], "event_id": 1}

data: {"chunk": " privacy", "risk_score": 0.0, "entities": [], "event_id": 2}

data: {"chunk": " involves", "risk_score": 0.0, "entities": [], "event_id": 3}

event: compliance_check
data: {"risk_score": 0.2, "triggered_rules": [], "safe": true}

event: complete
data: {"total_tokens": 150, "processing_time_ms": 2500, "final_risk_score": 0.2}
```

### GET /chat/stream (Legacy)

Legacy streaming endpoint with query parameters.

**Parameters**:
- `q` (required): Question/message to process

**Example**:
```bash
curl -N -H "Accept: text/event-stream" "http://localhost:8000/chat/stream?q=Hello"
```

## 📜 Audit & Logs

### GET /audit/logs

Retrieve audit logs with filtering options.

**Parameters**:
- `limit` (optional, default: 50): Number of logs to retrieve
- `offset` (optional, default: 0): Pagination offset
- `event_type` (optional): Filter by event type
- `start_date` (optional): Start date filter (ISO 8601)
- `end_date` (optional): End date filter (ISO 8601)

**Example Request**:
```bash
curl "http://localhost:8000/audit/logs?limit=10&event_type=compliance_check"
```

**Response**:
```json
{
  "logs": [
    {
      "id": 123,
      "timestamp": "2025-01-01T12:00:00Z",
      "event_type": "compliance_check",
      "session_id": "session_123",
      "compliance_type": "HIPAA",
      "risk_score": 0.8,
      "blocked": false,
      "decision_reason": "Risk score: 0.80 - Content processed successfully",
      "entities_detected": [
        {
          "type": "EMAIL_ADDRESS",
          "confidence": 0.95,
          "text": "***@***.com"
        }
      ],
      "patterns_detected": ["email"],
      "content_hash": "abc123...",
      "processing_time_ms": 45
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## 📊 Metrics & Monitoring

### GET /metrics/summary

Get compliance metrics summary.

**Response**:
```json
{
  "total_requests": 1500,
  "blocked_requests": 25,
  "block_rate": 0.0167,
  "avg_risk_score": 0.23,
  "top_violations": [
    {"type": "email", "count": 45},
    {"type": "phone", "count": 23},
    {"type": "ssn", "count": 12}
  ],
  "compliance_by_region": {
    "HIPAA": {"total": 500, "blocked": 15},
    "PCI": {"total": 300, "blocked": 8},
    "GDPR": {"total": 700, "blocked": 2}
  }
}
```

### POST /metrics/snapshot

Create a metrics snapshot (internal use).

**Request Body**:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "total_requests": 100,
  "blocked_requests": 5,
  "avg_response_time": 450
}
```

## 🧪 Testing Endpoints

### POST /test/run

Run compliance test suite.

**Request Body**:
```json
{
  "test_categories": ["pii", "phi", "pci"],
  "region": "HIPAA"
}
```

**Response**:
```json
{
  "test_results": {
    "pii": {
      "email": {"passed": true, "risk_score": 0.4},
      "phone": {"passed": true, "risk_score": 0.5},
      "ssn": {"passed": true, "risk_score": 1.2}
    },
    "phi": {
      "medical_record": {"passed": true, "risk_score": 1.0},
      "diagnosis": {"passed": true, "risk_score": 0.8}
    }
  },
  "summary": {
    "total_tests": 12,
    "passed": 12,
    "failed": 0,
    "success_rate": 1.0
  }
}
```

### GET /test/patterns

Get available test patterns.

**Response**:
```json
{
  "categories": {
    "pii": {
      "patterns": ["email", "phone", "ssn", "address"],
      "description": "Personally Identifiable Information"
    },
    "phi": {
      "patterns": ["medical_record", "diagnosis", "prescription"],
      "description": "Protected Health Information"
    },
    "pci": {
      "patterns": ["credit_card", "bank_account"],
      "description": "Payment Card Industry Data"
    }
  }
}
```

## 🔧 Debug Endpoints

### GET /debug/info

Get detailed system information (debug mode only).

**Response**:
```json
{
  "system": {
    "presidio_version": "2.2.354",
    "spacy_model": "en_core_web_lg",
    "tiktoken_version": "0.5.1",
    "openai_version": "1.3.5"
  },
  "models": {
    "loaded": ["en_core_web_lg"],
    "available": ["en_core_web_sm", "en_core_web_lg"]
  },
  "memory_usage": {
    "presidio": "1.2GB",
    "total": "2.1GB"
  }
}
```

### POST /debug/presidio

Test Presidio detection directly.

**Request Body**:
```json
{
  "text": "Contact John Doe at john@example.com or (555) 123-4567",
  "language": "en"
}
```

**Response**:
```json
{
  "entities": [
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 22,
      "end": 38,
      "score": 0.95,
      "text": "john@example.com"
    },
    {
      "entity_type": "PHONE_NUMBER", 
      "start": 42,
      "end": 56,
      "score": 0.85,
      "text": "(555) 123-4567"
    }
  ],
  "processing_time_ms": 23
}
```

## 🎨 Demo Endpoints

### POST /demo/generate-audit-data

Generate sample audit data for testing (development only).

**Request Body**:
```json
{
  "count": 100,
  "include_violations": true,
  "time_range_hours": 24
}
```

## 📝 Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "error": "Error description",
  "detail": "Detailed error message",
  "timestamp": "2025-01-01T12:00:00Z",
  "request_id": "req_123456"
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (invalid API key)
- **404**: Not Found (invalid endpoint)
- **422**: Unprocessable Entity (validation error)
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error
- **503**: Service Unavailable (system overloaded)

### Error Examples

**Invalid API Key**:
```json
{
  "error": "Invalid OpenAI API key",
  "detail": "The provided API key is not valid or has insufficient permissions",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

**Missing Required Parameter**:
```json
{
  "error": "Missing required parameter",
  "detail": "The 'text' parameter is required for risk assessment",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

**Rate Limit Exceeded**:
```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Please wait before making another request",
  "timestamp": "2025-01-01T12:00:00Z",
  "retry_after": 60
}
```

## 🔐 Security Considerations

### API Key Management
- API keys can be provided via request body or environment variables
- Keys are never logged or stored permanently
- Use environment variables for production deployments

### Rate Limiting
- Default: 100 requests per minute per IP
- Configurable via environment variables
- 429 status code returned when exceeded

### CORS Configuration
- Configurable allowed origins
- Default: All origins allowed (development)
- Restrict for production deployments

### Data Privacy
- Sensitive data is masked in logs
- PII/PHI content is hashed for audit trails
- No raw sensitive content stored permanently

## 📊 OpenAPI/Swagger Documentation

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

This comprehensive API documentation provides all the information needed to integrate with and test the compliance filtering system.
