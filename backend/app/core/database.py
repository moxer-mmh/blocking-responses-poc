"""
Database models and configuration for the restructured backend.
This replicates the exact database functionality from the original app.py.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    select,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

# Database base
Base = declarative_base()

# Database models (exact replicas from original app.py)
class AuditLog(Base):  # type: ignore
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), index=True)
    user_input_hash = Column(String(32))
    blocked_content_hash = Column(String(32), nullable=True)
    risk_score = Column(Float)
    triggered_rules = Column(Text)  # JSON string
    session_id = Column(String(64), index=True)
    processing_time_ms = Column(Float)
    presidio_entities = Column(Text, nullable=True)  # JSON string
    compliance_type = Column(String(20), nullable=True)
    user_id = Column(String(50), nullable=True, default="anonymous")
    decision_reason = Column(Text, nullable=True)

class MetricsSnapshot(Base):  # type: ignore
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    avg_risk_score = Column(Float, default=0.0)
    avg_processing_time = Column(Float, default=0.0)
    pattern_detections = Column(Text)  # JSON string
    presidio_detections = Column(Text)  # JSON string

# Database configuration (same as original)
DATABASE_URL = "sqlite+aiosqlite:///./compliance_audit.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Database initialization
async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Database operations
async def get_audit_logs(limit: int = 100, event_type: str = None):
    """Retrieve audit logs from database (exact replica from original app.py)"""
    try:
        async with async_session() as session:
            query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
            if event_type:
                query = query.where(AuditLog.event_type == event_type)
            
            result = await session.execute(query)
            audit_logs = result.scalars().all()
            
            # Convert to dict format (same as original)
            logs = []
            for log in audit_logs:
                log_dict = {
                    "id": f"audit_{log.id:06d}",
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "user_input_hash": log.user_input_hash,
                    "blocked_content_hash": log.blocked_content_hash,
                    "risk_score": log.risk_score,
                    "triggered_rules": json.loads(log.triggered_rules) if log.triggered_rules else [],
                    "session_id": log.session_id,
                    "processing_time_ms": log.processing_time_ms,
                    "presidio_entities": json.loads(log.presidio_entities) if log.presidio_entities else [],
                    "compliance_type": log.compliance_type,
                    "user_id": log.user_id or "anonymous",
                    "decision_reason": log.decision_reason
                }
                logs.append(log_dict)
            
            return logs
            
    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}")
        return []

async def save_audit_log(audit_data: dict):
    """Save audit log to database"""
    try:
        async with async_session() as session:
            db_audit = AuditLog(
                timestamp=datetime.fromisoformat(audit_data["timestamp"].replace("Z", "+00:00")) if isinstance(audit_data["timestamp"], str) else audit_data["timestamp"],
                event_type=audit_data["event_type"],
                user_input_hash=audit_data["user_input_hash"],
                blocked_content_hash=audit_data.get("blocked_content_hash"),
                risk_score=audit_data["risk_score"],
                triggered_rules=str(audit_data.get("triggered_rules", [])),
                session_id=audit_data["session_id"],
                processing_time_ms=audit_data.get("processing_time_ms", 0.0),
                presidio_entities=str(audit_data.get("presidio_entities", [])),
                compliance_type=audit_data.get("compliance_type"),
                user_id=audit_data.get("user_id", "anonymous"),
                decision_reason=audit_data.get("decision_reason")
            )
            session.add(db_audit)
            await session.commit()
            logger.info(f"Audit log saved: {audit_data['event_type']}")
            
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")

async def save_metrics_snapshot(metrics_data: dict):
    """Save metrics snapshot to database"""
    try:
        async with async_session() as session:
            snapshot = MetricsSnapshot(
                timestamp=datetime.utcnow(),
                total_requests=metrics_data.get("total_requests", 0),
                blocked_requests=metrics_data.get("blocked_requests", 0), 
                avg_risk_score=metrics_data.get("avg_risk_score", 0.0),
                avg_processing_time=metrics_data.get("avg_processing_time", 0.0),
                pattern_detections=str(metrics_data.get("pattern_detections", {})),
                presidio_detections=str(metrics_data.get("presidio_detections", {}))
            )
            session.add(snapshot)
            await session.commit()
            logger.info("Metrics snapshot saved")
            
    except Exception as e:
        logger.error(f"Failed to save metrics snapshot: {e}")
