# Streaming API Documentation

## Overview

The `/chat/stream` endpoint provides real-time content filtering and compliance monitoring using Server-Sent Events (SSE).

## Demo Mode

When no valid OpenAI API key is configured, the system automatically runs in demo mode with realistic compliance scenarios.

## Endpoint

```
POST /chat/stream
```

## Request Format

```json
{
  "message": "Your message to process",
  "delay_tokens": 5,        // Optional: Buffer size (min: 5, max: 100)
  "delay_ms": 100,          // Optional: Delay between tokens (min: 50, max: 2000)
  "risk_threshold": 1.0,    // Optional: Risk threshold for blocking (0.0-5.0)
  "model": "gpt-4o-mini",   // Optional: OpenAI model
  "region": "HIPAA"         // Optional: Compliance region
}
```

### Field Validation

- `message`: Required, 1-10000 characters
- `delay_tokens`: Optional, 5-100 (default: 24)
- `delay_ms`: Optional, 50-2000ms (default: 250)
- `risk_threshold`: Optional, 0.0-5.0 (default: 1.0)

## Response Format

The API returns Server-Sent Events with different event types:

### Chunk Event
```
event: chunk
id: 1
data: {
  "type": "chunk",
  "content": "token ",
  "risk_score": 0.1,
  "cumulative_risk": 0.1,
  "entities": ["PERSON"],
  "patterns": ["NAME_PATTERN"],
  "session_id": "abc123"
}
```

### Risk Alert Event
```
event: risk_alert
id: 2
data: {
  "type": "risk_alert",
  "content": "John",
  "risk_score": 0.9,
  "entities": ["PERSON"],
  "patterns": ["NAME_PATTERN"],
  "reason": "High-risk token detected: PERSON"
}
```

### Blocked Event
```
event: blocked
id: 3
data: {
  "type": "blocked",
  "reason": "Cumulative risk score 1.20 exceeded threshold 1.0",
  "risk_score": 1.2,
  "session_id": "abc123",
  "triggered_entities": ["US_SSN"],
  "compliance_violation": "HIPAA - PHI disclosure detected"
}
```

### Completion Event
```
event: completed
id: 4
data: {
  "type": "completed",
  "session_id": "abc123",
  "total_risk": 0.8,
  "status": "success"
}
```

## JavaScript Example

```javascript
const response = await fetch('http://localhost:8000/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Tell me about patient John Doe',
    delay_tokens: 5,
    delay_ms: 100,
    risk_threshold: 1.0
  })
})

const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  const chunk = decoder.decode(value)
  const lines = chunk.split('\n')

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = JSON.parse(line.slice(6))
        
        switch (data.type) {
          case 'chunk':
            console.log('Token:', data.content, 'Risk:', data.risk_score)
            break
          case 'risk_alert':
            console.warn('Risk Alert:', data.reason)
            break
          case 'blocked':
            console.error('Blocked:', data.reason)
            break
          case 'completed':
            console.log('Completed:', data.session_id)
            break
        }
      } catch (e) {
        console.warn('Failed to parse:', line)
      }
    }
  }
}
```

## curl Example

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about patient John Doe with SSN 123-45-6789",
    "delay_tokens": 5,
    "delay_ms": 100,
    "risk_threshold": 1.0
  }' \
  --no-buffer
```

## Python Example

```python
import requests
import json

def stream_chat(message):
    response = requests.post(
        'http://localhost:8000/chat/stream',
        json={
            'message': message,
            'delay_tokens': 5,
            'delay_ms': 100,
            'risk_threshold': 1.0
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line.startswith(b'data: '):
            try:
                data = json.loads(line[6:])
                if data['type'] == 'chunk':
                    print(data['content'], end='', flush=True)
                elif data['type'] == 'blocked':
                    print(f"\n[BLOCKED: {data['reason']}]")
                    break
                elif data['type'] == 'completed':
                    print(f"\n[COMPLETED: {data['session_id']}]")
                    break
            except json.JSONDecodeError:
                pass

# Usage
stream_chat("Tell me about medical records")
```

## Demo Mode Scenarios

When running in demo mode, the system simulates:

1. **Normal Content**: Low risk scores (0.1)
2. **Medical Terms**: Medium risk (0.7) - "patient", "medical", "record"
3. **Personal Names**: High risk (0.9) - "John", "Doe"
4. **SSN Patterns**: Critical risk (1.2) - "123-45-6789"
5. **Phone Numbers**: High risk (0.8) - "(555) 123-4567"
6. **Dates**: Medium risk (0.6) - Birth dates

## Risk Scoring

- **0.0-0.3**: Safe content
- **0.3-0.7**: Caution - potential sensitive content
- **0.7-1.0**: High risk - likely sensitive information
- **1.0+**: Critical - triggers blocking

## Compliance Features

- **Real-time Analysis**: Token-by-token risk assessment
- **Buffered Streaming**: Look-ahead window for context analysis
- **Audit Logging**: All decisions logged for compliance
- **Configurable Thresholds**: Adjustable risk tolerance
- **Pattern Detection**: Regex and ML-based entity recognition
- **Session Tracking**: Unique session IDs for audit trails

## Error Handling

- **422 Unprocessable Entity**: Invalid request format or validation errors
- **500 Internal Server Error**: Server-side processing errors
- **Connection drops**: Client should implement reconnection logic

## Best Practices

1. Always validate the `delay_tokens` parameter (minimum 5)
2. Handle all event types in your client
3. Implement proper error handling for network issues
4. Use appropriate `risk_threshold` for your use case
5. Monitor session IDs for audit compliance
6. Implement client-side buffering for smooth UI updates
