"""Database models for the application."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.database import Base


class AuditLog(Base):
    """Audit log model for compliance tracking."""
    
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50), nullable=False)
    user_input_hash = Column(String(32), nullable=False)
    blocked_content_hash = Column(String(32), nullable=True)
    risk_score = Column(Float, nullable=False)
    triggered_rules = Column(Text, nullable=False)  # JSON string
    session_id = Column(String(32), nullable=True)
    compliance_region = Column(String(20), nullable=True)
    presidio_entities = Column(Text, nullable=True)  # JSON string
    processing_time_ms = Column(Float, nullable=True)


class MetricsSnapshot(Base):
    """Metrics snapshot model for performance tracking."""
    
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_requests = Column(Integer, nullable=False)
    blocked_requests = Column(Integer, nullable=False)
    block_rate = Column(Float, nullable=False)
    avg_risk_score = Column(Float, nullable=False)
    avg_processing_time = Column(Float, nullable=False)
    pattern_detections = Column(Text, nullable=False)  # JSON string
    presidio_detections = Column(Text, nullable=False)  # JSON string
