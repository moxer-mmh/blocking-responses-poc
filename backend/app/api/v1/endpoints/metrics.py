"""Metrics and monitoring endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from app.services.metrics import MetricsTracker
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize metrics service
metrics = MetricsTracker()


@router.get("/")
async def get_metrics():
    """Get real-time system metrics."""
    return {
        "total_requests": metrics.total_requests,
        "blocked_requests": metrics.blocked_requests,
        "block_rate": metrics.block_rate,
        "avg_risk_score": metrics.avg_risk_score,
        "pattern_detections": dict(metrics.pattern_detections),
        "presidio_detections": dict(metrics.presidio_detections),
        "performance_metrics": {
            "avg_processing_time": metrics.avg_processing_time,
            "avg_response_time": metrics.avg_response_time,
            "requests_per_second": metrics.requests_per_second,
            "error_rate": metrics.error_rate,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": metrics.uptime_seconds if hasattr(metrics, 'uptime_seconds') else 0
    }


@router.get("/summary")
async def get_metrics_summary():
    """Get metrics summary with additional context."""
    summary = metrics.get_metrics_summary()
    return {
        **summary,
        "compliance_status": {
            "risk_threshold": settings.risk_threshold,
            "current_avg_risk": summary.get("avg_risk_score", 0),
            "status": "healthy" if summary.get("avg_risk_score", 0) < settings.risk_threshold else "elevated"
        },
        "system_health": {
            "requests_per_second": summary.get("requests_per_second", 0),
            "error_rate": summary.get("error_rate", 0),
            "avg_processing_time": summary.get("avg_processing_time", 0)
        }
    }


@router.post("/snapshot")
async def create_metrics_snapshot():
    """Create a snapshot of current metrics for historical tracking."""
    # This would typically save to database
    snapshot_data = metrics.get_metrics_summary()
    
    # Add snapshot metadata
    snapshot_data.update({
        "snapshot_id": f"snapshot_{int(datetime.utcnow().timestamp())}",
        "created_at": datetime.utcnow().isoformat(),
        "type": "manual_snapshot"
    })
    
    logger.info(f"Metrics snapshot created: {snapshot_data['snapshot_id']}")
    
    return {
        "message": "Metrics snapshot created successfully",
        "snapshot": snapshot_data
    }


@router.get("/health")
async def get_system_health():
    """Get overall system health based on metrics."""
    summary = metrics.get_metrics_summary()
    
    # Determine health status
    health_score = 100
    warnings = []
    
    # Check error rate
    if summary.get("error_rate", 0) > 5:
        health_score -= 20
        warnings.append("High error rate detected")
    
    # Check average processing time
    if summary.get("avg_processing_time", 0) > 1000:  # 1 second
        health_score -= 15
        warnings.append("High processing time detected")
    
    # Check block rate
    block_rate = summary.get("block_rate", 0)
    if block_rate > 50:
        health_score -= 10
        warnings.append("High block rate - potential compliance issues")
    elif block_rate > 20:
        health_score -= 5
        warnings.append("Elevated block rate")
    
    # Determine status
    if health_score >= 90:
        status = "excellent"
    elif health_score >= 75:
        status = "good"
    elif health_score >= 60:
        status = "fair"
    else:
        status = "poor"
    
    return {
        "status": status,
        "health_score": health_score,
        "warnings": warnings,
        "metrics_summary": summary,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/snapshot")
async def create_metrics_snapshot():
    """Create a snapshot of current metrics."""
    try:
        from datetime import datetime
        import uuid
        
        # Get current metrics
        current_metrics = metrics.get_metrics_summary()
        
        # Create snapshot
        snapshot = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": current_metrics,
            "metadata": {
                "version": settings.version,
                "uptime_seconds": current_metrics.get("uptime_seconds", 0),
                "created_by": "system"
            }
        }
        
        # In a real implementation, this would be saved to a database
        # For now, just return the snapshot
        return {
            "snapshot": snapshot,
            "message": "Metrics snapshot created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create metrics snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")
