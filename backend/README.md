# Blocking Responses API - Backend

This is the backend service for the Blocking Responses API, providing PII/PHI/PCI compliance for AI applications.

## Quick Start

### Development Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -e ".[dev]"
   ```

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Run the Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Setup

1. **Build and Run**
   ```bash
   docker-compose up --build
   ```

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API route definitions
│   │   ├── deps.py         # API dependencies
│   │   └── v1/             # API version 1
│   │       ├── api.py      # Main API router
│   │       └── endpoints/  # Individual endpoint modules
│   ├── core/               # Core configuration
│   │   ├── config.py       # Settings and configuration
│   │   └── security.py     # Security utilities
│   ├── crud/               # Database CRUD operations
│   ├── db/                 # Database configuration
│   │   └── database.py     # Database setup
│   ├── models/             # SQLAlchemy models
│   │   └── audit.py        # Audit and metrics models
│   ├── schemas/            # Pydantic schemas
│   │   └── requests.py     # Request/response schemas
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   └── main.py            # FastAPI application entry point
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── end_to_end/        # End-to-end tests
├── docker-compose.yml     # Docker compose configuration
├── Dockerfile            # Docker image definition
├── pyproject.toml        # Python project configuration
└── requirements.txt      # Python dependencies
```

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Async/Await Support**: Full asynchronous request handling
- **Automatic Documentation**: Interactive API docs at `/docs`
- **Pydantic Validation**: Request/response validation and serialization
- **SQLAlchemy ORM**: Database operations with async support
- **Compliance Monitoring**: Real-time PII/PHI/PCI detection
- **Audit Logging**: Complete compliance audit trail
- **Rate Limiting**: Built-in request rate limiting
- **CORS Support**: Cross-origin resource sharing configuration

## API Endpoints

- `GET /health` - Health check
- `POST /chat/stream` - Stream chat with compliance filtering
- `POST /assess-risk` - Assess text compliance risk
- `GET /audit-logs` - Retrieve audit logs
- `GET /metrics` - Get compliance metrics
- `GET /config` - Get current configuration

## Configuration

Environment variables can be set in `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4o-mini
RISK_THRESHOLD=0.7
LOG_LEVEL=INFO
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
```

## Development

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Type checking
mypy app

# Lint code
flake8 app tests
```
