"""API dependencies and dependency injection."""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
from app.core.config import settings
from app.core.security import get_valid_api_key


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_session():
        yield session


def get_settings():
    """Get application settings dependency."""
    return settings


async def verify_api_key(api_key: str = None) -> str:
    """Verify API key dependency."""
    valid_key = get_valid_api_key(api_key)
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OpenAI API key required"
        )
    return valid_key
