"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema with validation."""
    
    message: str = Field(..., min_length=1, max_length=5000)
    model: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None, max_length=1000)
    delay_tokens: Optional[int] = Field(None, ge=5, le=50)
    delay_ms: Optional[int] = Field(None, ge=50, le=1000)
    risk_threshold: Optional[float] = Field(None, ge=0.0, le=2.0)
    enable_safe_rewrite: Optional[bool] = None
    region: Optional[str] = Field(
        None, description="Compliance region: US, EU, HIPAA, PCI", max_length=10
    )
    api_key: Optional[str] = Field(
        None, description="OpenAI API key (overrides environment variable)", max_length=200
    )
    # New sliding window parameters
    analysis_window_size: Optional[int] = Field(None, ge=50, le=500)
    analysis_frequency: Optional[int] = Field(None, ge=5, le=100)


class ComplianceResult(BaseModel):
    """Compliance analysis result schema."""
    
    score: float
    blocked: bool
    triggered_rules: List[str]
    presidio_entities: List[Dict[str, Any]] = []
    snippet_hash: Optional[str] = None
    compliance_region: Optional[str] = None
    timestamp: datetime


class AuditEvent(BaseModel):
    """Audit event schema for logging."""
    
    event_type: str
    user_input_hash: str
    blocked_content_hash: Optional[str] = None
    risk_score: float
    triggered_rules: List[str]
    timestamp: datetime
    session_id: Optional[str] = None


class WindowAnalysisResult(BaseModel):
    """Window analysis result schema."""
    
    window_text: str
    window_start: int
    window_end: int
    window_size: int
    pattern_score: float
    presidio_score: float
    total_score: float
    triggered_rules: List[str]
    presidio_entities: List[Dict[str, Any]]
    blocked: bool
    timestamp: str
    analysis_position: int


class AnalysisConfig(BaseModel):
    """Analysis configuration schema."""
    
    analysis_window_size: int
    analysis_overlap: int
    analysis_frequency: int
    risk_threshold: float
    delay_tokens: int
    delay_ms: int


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str
    timestamp: str
    version: str
    dependencies: Dict[str, bool]
    compliance_features: Dict[str, bool]
