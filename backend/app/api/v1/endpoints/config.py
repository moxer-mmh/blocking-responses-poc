"""Configuration endpoints."""

import logging
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_config():
    """Get general system configuration."""
    return {
        "delay_tokens": settings.delay_tokens,
        "delay_ms": settings.delay_ms,
        "risk_threshold": settings.risk_threshold,
        "default_model": settings.default_model,
        "judge_model": settings.judge_model,
        "enable_judge": settings.enable_judge,
        "judge_threshold": settings.judge_threshold,
        "enable_safe_rewrite": settings.enable_safe_rewrite,
        # Sliding window configuration
        "analysis_window_size": settings.analysis_window_size,
        "analysis_overlap": settings.analysis_overlap,
        "analysis_frequency": settings.analysis_frequency,
        # CORS configuration (sanitized)
        "cors_origins": "*" if settings.cors_origins == "*" else "configured",
        "version": "1.1.0-restructured"
    }


@router.get("/environment")
async def get_environment_info():
    """Get environment and dependency information."""
    # Check dependencies
    dependencies = {}
    
    # Check tiktoken
    try:
        import tiktoken
        dependencies["tiktoken"] = {
            "available": True,
            "version": getattr(tiktoken, "__version__", "unknown")
        }
    except ImportError:
        dependencies["tiktoken"] = {"available": False}
    
    # Check presidio
    try:
        from presidio_analyzer import __version__ as presidio_version
        dependencies["presidio"] = {
            "available": True,
            "version": presidio_version
        }
    except ImportError:
        dependencies["presidio"] = {"available": False}
    
    # Check OpenAI configuration
    dependencies["openai"] = {
        "configured": bool(settings.openai_api_key),
        "model": settings.default_model
    }
    
    return {
        "environment": "restructured",
        "log_level": settings.log_level,
        "dependencies": dependencies,
        "features": {
            "sliding_window_analysis": True,
            "real_time_compliance": True,
            "audit_logging": True,
            "safe_rewrite": settings.enable_safe_rewrite,
            "llm_judge": settings.enable_judge
        }
    }
