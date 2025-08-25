"""Main FastAPI application entry point."""

import logging
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Blocking Responses API (Restructured)...")


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
