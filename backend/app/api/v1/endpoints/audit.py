"""
Audit log endpoints for the restructured backend.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import random

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_audit_logs(
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    action: Optional[str] = Query(None, description="Filter by action type")
):
    """Get audit logs with optional filtering."""
    try:
        # Mock audit logs for demonstration
        mock_logs = []
        actions = ["compliance_check", "pii_detection", "risk_assessment", "text_analysis", "pattern_match"]
        levels = ["INFO", "WARNING", "ERROR"]
        
        # Generate mock audit logs
        for i in range(min(limit, 50)):  # Limit to 50 for demo
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 48))
            log_entry = {
                "id": f"audit_{i + offset + 1:06d}",
                "timestamp": timestamp.isoformat(),
                "level": random.choice(levels),
                "action": random.choice(actions),
                "user_id": f"user_{random.randint(1000, 9999)}",
                "session_id": f"session_{random.randint(100000, 999999)}",
                "message": f"Processed request with {random.choice(actions)} action",
                "metadata": {
                    "ip_address": f"192.168.1.{random.randint(1, 254)}",
                    "user_agent": "Mozilla/5.0 (compatible)",
                    "request_id": f"req_{random.randint(100000, 999999)}",
                    "processing_time_ms": random.randint(50, 500)
                }
            }
            
            # Apply filters
            if level and log_entry["level"] != level.upper():
                continue
            if action and log_entry["action"] != action:
                continue
                
            mock_logs.append(log_entry)
        
        return {
            "logs": mock_logs,
            "total": len(mock_logs),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance")
async def get_compliance_audit_logs(
    limit: int = Query(100, description="Maximum number of logs to return"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)")
):
    """Get compliance-specific audit logs."""
    try:
        # Mock compliance audit logs
        mock_logs = []
        compliance_actions = [
            "pii_detected", "sensitive_data_blocked", "compliance_violation", 
            "safe_rewrite_applied", "risk_threshold_exceeded"
        ]
        
        for i in range(min(limit, 30)):
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
            
            # Apply date filters if provided
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if timestamp < start_dt:
                    continue
                    
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if timestamp > end_dt:
                    continue
            
            log_entry = {
                "id": f"compliance_audit_{i + 1:06d}",
                "timestamp": timestamp.isoformat(),
                "action": random.choice(compliance_actions),
                "severity": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "entity_types": random.sample(["PERSON", "EMAIL", "SSN", "PHONE", "CREDIT_CARD"], 
                                            random.randint(1, 3)),
                "risk_score": round(random.uniform(0.1, 1.0), 3),
                "blocked": random.choice([True, False]),
                "compliance_region": random.choice(["GDPR", "HIPAA", "PCI_DSS", "SOX"]),
                "metadata": {
                    "text_length": random.randint(50, 500),
                    "processing_time_ms": random.randint(100, 800),
                    "model_used": random.choice(["gpt-4o-mini", "gpt-4"]),
                    "confidence_score": round(random.uniform(0.7, 0.99), 3)
                }
            }
            mock_logs.append(log_entry)
        
        return {
            "compliance_logs": mock_logs,
            "total": len(mock_logs),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_violations": sum(1 for log in mock_logs if log["blocked"]),
                "avg_risk_score": round(sum(log["risk_score"] for log in mock_logs) / len(mock_logs), 3) if mock_logs else 0,
                "compliance_regions": list(set(log["compliance_region"] for log in mock_logs))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/generate-audit-data")
async def generate_demo_audit_data():
    """Generate demo audit data for testing."""
    try:
        # This would normally populate a database with demo data
        # For now, just return success message
        return {
            "message": "Demo audit data generated successfully",
            "records_created": random.randint(50, 200),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate demo audit data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
