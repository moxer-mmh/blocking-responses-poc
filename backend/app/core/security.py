"""Security utilities and authentication."""

import secrets
import hashlib
from typing import Optional


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID."""
    return secrets.token_urlsafe(32)


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging purposes."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def get_valid_api_key(provided_api_key: Optional[str] = None) -> Optional[str]:
    """Get a valid API key, prioritizing provided key over environment variable.
    
    Args:
        provided_api_key: API key provided in request
        
    Returns:
        Valid API key or None if none available
    """
    from app.core.config import settings
    
    if provided_api_key and provided_api_key.strip():
        return provided_api_key.strip()
    
    if settings.openai_api_key and settings.openai_api_key.strip():
        return settings.openai_api_key.strip()
    
    return None
