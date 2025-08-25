"""API v1 router."""

from fastapi import APIRouter

# Import endpoint modules
# from app.api.v1.endpoints import chat, compliance, metrics

api_router = APIRouter()

# Include endpoint routers
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
# api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

# For now, add a simple endpoint
@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "Blocking Responses API v1"}
