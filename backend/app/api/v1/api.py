"""API v1 router."""

from fastapi import APIRouter

# Import endpoint modules
from app.api.v1.endpoints import chat, compliance, metrics, config, testing, audit

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(testing.router, prefix="/test", tags=["testing"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])

# Add some root level endpoints for backward compatibility
@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Blocking Responses API v1 (Restructured)",
        "version": "1.1.0",
        "endpoints": {
            "chat": "/api/v1/chat/",
            "compliance": "/api/v1/compliance/", 
            "metrics": "/api/v1/metrics/",
            "config": "/api/v1/config/",
            "testing": "/api/v1/test/",
            "audit": "/api/v1/audit-logs/"
        },
        "legacy_compatibility": "Available at root level",
        "documentation": "/docs"
    }
