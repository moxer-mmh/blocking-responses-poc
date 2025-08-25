"""API v1 endpoints package."""

from .chat import router as chat_router

__all__ = ["chat_router"]
