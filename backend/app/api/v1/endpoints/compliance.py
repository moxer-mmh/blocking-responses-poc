"""Compliance analysis and risk assessment endpoints."""

import logging
from time import monotonic
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.services.compliance import RegulatedPatternDetector
from app.services.presidio_service import PresidioDetector
from app.services.metrics import MetricsTracker

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
pattern_detector = RegulatedPatternDetector()
presidio_detector = PresidioDetector()
metrics = MetricsTracker()


class AnalyzeTextRequest(BaseModel):
    text: str
    region: Optional[str] = None


@router.post("/assess-risk")
async def assess_compliance_risk(
    text: str = Query(..., description="Text to analyze for compliance risks"),
    region: Optional[str] = Query(None, description="Compliance region (HIPAA, PCI, GDPR, CCPA)")
):
    """Comprehensive compliance risk assessment."""
    start_time = monotonic()

    # Pattern-based assessment
    compliance_result = pattern_detector.assess_compliance_risk(text, region)

    # Presidio-based assessment
    presidio_score, presidio_entities = presidio_detector.analyze_text(text)

    # Combine results
    total_score = compliance_result.score + presidio_score
    is_blocked = total_score >= settings.risk_threshold

    # Record metrics
    processing_time = (monotonic() - start_time) * 1000  # Convert to ms
    metrics.record_request(
        blocked=is_blocked, delay_ms=processing_time, risk_score=total_score
    )

    # Record pattern detections
    for rule in compliance_result.triggered_rules:
        pattern_name = rule.split(":")[0].strip()
        metrics.record_pattern_detection(pattern_name)

    # Record Presidio detections
    for entity in presidio_entities:
        metrics.record_presidio_detection(entity.get("entity_type", "unknown"))

    return {
        "score": total_score,
        "blocked": is_blocked,
        "pattern_score": compliance_result.score,
        "presidio_score": presidio_score,
        "triggered_rules": compliance_result.triggered_rules,
        "presidio_entities": presidio_entities,
        "compliance_region": region,
        "snippet_hash": compliance_result.snippet_hash,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/analyze-text")
async def analyze_text_compliance(request: AnalyzeTextRequest):
    """Analyze text for compliance issues - for testing and debugging."""
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    start_time = monotonic()

    # Pattern-based assessment
    compliance_result = pattern_detector.assess_compliance_risk(request.text, request.region)

    # Presidio-based assessment
    presidio_score, presidio_entities = presidio_detector.analyze_text(request.text)

    # Combine results
    total_score = compliance_result.score + presidio_score
    is_blocked = total_score >= settings.risk_threshold
    
    processing_time = (monotonic() - start_time) * 1000

    return {
        "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
        "analysis": {
            "total_score": total_score,
            "pattern_score": compliance_result.score,
            "presidio_score": presidio_score,
            "blocked": is_blocked,
            "processing_time_ms": processing_time
        },
        "details": {
            "triggered_rules": compliance_result.triggered_rules,
            "presidio_entities": presidio_entities,
            "compliance_region": request.region,
            "risk_threshold": settings.risk_threshold
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/patterns")
async def get_compliance_patterns():
    """Get available compliance patterns and rules."""
    return {
        "patterns": {
            "PII": ["email", "phone", "ssn", "dob", "address"],
            "PHI": ["medical_record", "diagnosis", "medication"],
            "PCI": ["credit_card", "iban", "routing_number", "bank_account"],
            "Security": ["password", "api_key", "secret"]
        },
        "regions": ["HIPAA", "PCI", "GDPR", "CCPA"],
        "current_threshold": settings.risk_threshold,
        "presidio_available": presidio_detector.is_available()
    }


@router.get("/config")
async def get_compliance_config():
    """Get current compliance configuration."""
    return {
        "risk_threshold": settings.risk_threshold,
        "presidio_confidence_threshold": settings.presidio_confidence_threshold,
        "judge_threshold": settings.judge_threshold,
        "enable_judge": settings.enable_judge,
        "enable_safe_rewrite": settings.enable_safe_rewrite,
        "presidio_available": presidio_detector.is_available()
    }


@router.get("/analysis-config")
async def get_analysis_config():
    """Get sliding window analysis configuration with performance estimates."""
    return {
        "current_config": {
            "analysis_window_size": settings.analysis_window_size,
            "analysis_overlap": settings.analysis_overlap,
            "analysis_frequency": settings.analysis_frequency,
            "risk_threshold": settings.risk_threshold,
            "delay_tokens": settings.delay_tokens,
            "delay_ms": settings.delay_ms
        },
        "config_limits": {
            "analysis_window_size": {
                "min": 50,
                "max": 500,
                "default": 150
            },
            "analysis_overlap": {
                "min": 10,
                "max": 100,
                "default": 50
            },
            "analysis_frequency": {
                "min": 5,
                "max": 100,
                "default": 25
            },
            "risk_threshold": {
                "min": 0.1,
                "max": 2.0,
                "default": 0.7
            },
            "delay_tokens": {
                "min": 5,
                "max": 100,
                "default": 24
            },
            "delay_ms": {
                "min": 50,
                "max": 2000,
                "default": 250
            }
        },
        "performance_estimates": {
            "old_approach_cost": "1 analysis per token",
            "new_approach_cost": f"1 analysis per {settings.analysis_frequency} tokens",
            "efficiency_gain": f"{settings.analysis_frequency}x reduction in analysis calls",
            "context_improvement": f"{settings.analysis_window_size} token context vs single token"
        }
    }
