"""
Shared service instances - maintains global state like original app.py
This ensures metrics continuity and proper state management.
"""

import logging
from app.services.compliance import RegulatedPatternDetector
from app.services.presidio_service import PresidioDetector
from app.services.metrics import MetricsTracker
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global service instances (same as original app.py)
# These are initialized once and shared across all endpoints
metrics = None
pattern_detector = None
presidio_detector = None


def initialize_services():
    """Initialize shared service instances on app startup."""
    global metrics, pattern_detector, presidio_detector
    
    try:
        # Initialize metrics tracker
        metrics = MetricsTracker()
        logger.info("MetricsTracker initialized")
        
        # Initialize pattern detector
        pattern_detector = RegulatedPatternDetector()
        logger.info("RegulatedPatternDetector initialized")
        
        # Initialize Presidio detector  
        presidio_detector = PresidioDetector()
        logger.info("PresidioDetector initialized")
        
        logger.info("All shared services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


def get_metrics() -> MetricsTracker:
    """Get the shared metrics tracker instance."""
    if metrics is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return metrics


def get_pattern_detector() -> RegulatedPatternDetector:
    """Get the shared pattern detector instance.""" 
    if pattern_detector is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return pattern_detector


def get_presidio_detector() -> PresidioDetector:
    """Get the shared Presidio detector instance."""
    if presidio_detector is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    return presidio_detector


# Service health check
def check_services_health() -> dict:
    """Check health of all shared services."""
    health = {
        "metrics": metrics is not None,
        "pattern_detector": pattern_detector is not None, 
        "presidio_detector": presidio_detector is not None,
        "all_healthy": False
    }
    
    health["all_healthy"] = all(health.values())
    return health
