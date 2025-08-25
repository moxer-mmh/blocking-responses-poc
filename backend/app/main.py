"""Main FastAPI application entry point."""

import logging
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Basic configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("blocking_responses_regulated")

# Create FastAPI app
app = FastAPI(
    title="Blocking Responses API - Regulated Edition (Restructured)",
    description="Production-ready SSE proxy with PII/PHI/PCI compliance for regulated industries",
    version="1.1.0",
)

# Rate limiting setup (same as original)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
def get_cors_origins():
    """Get CORS origins from environment."""
    if not CORS_ORIGINS:
        return ["http://localhost:3000", "http://localhost:80"]
    return [origin.strip() for origin in CORS_ORIGINS.split(",")]

origins = get_cors_origins()
allow_credentials = "*" not in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

# Add legacy endpoints for backward compatibility
from app.api.v1.endpoints import compliance, metrics, config, testing, audit, chat

# Root level endpoints (backward compatibility)
app.include_router(chat.router, prefix="/chat", tags=["chat-legacy"])  # Add root-level chat
app.include_router(compliance.router, prefix="/compliance", tags=["compliance-legacy"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics-legacy"])  
app.include_router(config.router, prefix="/config", tags=["config-legacy"])
app.include_router(testing.router, prefix="/test", tags=["testing-legacy"])
app.include_router(audit.router, prefix="/audit-logs", tags=["audit-legacy"])

# Add specific legacy endpoints that were at root level
@app.get("/assess-risk")
async def legacy_assess_risk():
    """Legacy endpoint redirect."""
    from fastapi import Request
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/compliance/assess-risk")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Blocking Responses API (Restructured)...")
    
    # Initialize shared services (same as original app.py)
    try:
        from app.core.services import initialize_services
        initialize_services()
        logger.info("Shared services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize shared services: {e}")
        raise
    
    # Initialize database
    try:
        from app.core.database import init_database
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Blocking Responses API...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    # Check dependencies
    dependencies = {}
    
    # Check tiktoken
    try:
        import tiktoken
        dependencies["tiktoken"] = True
    except ImportError:
        dependencies["tiktoken"] = False
    
    # Check presidio
    try:
        from presidio_analyzer import AnalyzerEngine
        dependencies["presidio"] = True
    except ImportError:
        dependencies["presidio"] = False
    
    # Check OpenAI configuration
    openai_key = os.getenv("OPENAI_API_KEY", "")
    dependencies["openai_configured"] = bool(openai_key)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0-restructured",
        "dependencies": dependencies,
        "compliance_features": {
            "audit_logging": True,
            "safe_rewrite": True,
            "hash_sensitive_data": True,
        },
        "note": "This is the restructured backend - original endpoints will be migrated gradually"
    }


# Legacy assess-risk endpoint at root level
@app.post("/assess-risk")
async def legacy_assess_risk(text: str, region: str = None):
    """Legacy assess-risk endpoint for backward compatibility."""
    from app.api.v1.endpoints.compliance import assess_compliance_risk
    return await assess_compliance_risk(text, region)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Blocking Responses API - Regulated Edition (Restructured)", 
        "version": "1.1.0",
        "status": "Backend structure successfully reorganized",
        "original_api": "http://localhost:8000 (still running)",
        "next_steps": "Migrate endpoints from original app.py to new structure"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port for testing
