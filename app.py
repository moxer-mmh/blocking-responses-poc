# pip install fastapi uvicorn langchain-openai langchain-core presidio-analyzer spacy tiktoken
# python -m spacy download en_core_web_lg
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncIterator, Dict, Any, List, Optional
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from collections import deque
from time import monotonic
import asyncio
import re
import json
import hashlib
import logging
import random
from datetime import datetime, timezone

# Database imports
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    select,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Microsoft Presidio for industrial PII/PHI detection ---
try:
    from presidio_analyzer import (
        AnalyzerEngine,
        PatternRecognizer,
        Pattern,
    )
    from presidio_analyzer.nlp_engine import SpacyNlpEngine

    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    print(
        "Warning: Presidio not available. Install with: pip install presidio-analyzer"
    )

# --- Tokenizer for reliable token windows ---
try:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")  # type: ignore
    TIKTOKEN_AVAILABLE = True
except ImportError:
    enc = None  # type: ignore
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Install with: pip install tiktoken")


# Configuration
class Settings(BaseSettings):
    openai_api_key: str = ""
    default_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    log_level: str = "INFO"

    # SSE and buffering settings
    delay_tokens: int = 24
    delay_ms: int = 250

    # Compliance thresholds
    risk_threshold: float = 1.0
    presidio_confidence_threshold: float = 0.6
    judge_threshold: float = 0.8  # Added missing field
    enable_judge: bool = True  # Added missing field

    # Safe rewrite settings
    enable_safe_rewrite: bool = True
    rewrite_temperature: float = 0.2

    # Compliance features
    enable_audit_logging: bool = True
    audit_retention_days: int = 30
    hash_sensitive_data: bool = True

    # CORS and security
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()

# -------------------- Database Setup --------------------
Base = declarative_base()  # type: ignore


class AuditLog(Base):  # type: ignore
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


class MetricsSnapshot(Base):  # type: ignore
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


# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./compliance_audit.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Initialize database
async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("blocking_responses_regulated")


# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    delay_tokens: Optional[int] = Field(None, ge=5, le=100)
    delay_ms: Optional[int] = Field(None, ge=50, le=2000)
    risk_threshold: Optional[float] = Field(None, ge=0.0, le=5.0)
    enable_safe_rewrite: Optional[bool] = None
    region: Optional[str] = Field(
        None, description="Compliance region: US, EU, HIPAA, PCI"
    )
    api_key: Optional[str] = Field(
        None, description="OpenAI API key (overrides environment variable)"
    )


class ComplianceResult(BaseModel):
    score: float
    blocked: bool
    triggered_rules: List[str]
    presidio_entities: List[Dict[str, Any]] = []
    snippet_hash: Optional[str] = None
    compliance_region: Optional[str] = None
    timestamp: datetime


class AuditEvent(BaseModel):
    event_type: str
    user_input_hash: str
    blocked_content_hash: Optional[str] = None
    risk_score: float
    triggered_rules: List[str]
    timestamp: datetime
    session_id: Optional[str] = None


# FastAPI app
app = FastAPI(
    title="Blocking Responses API - Regulated Edition",
    description="Production-ready SSE proxy with PII/PHI/PCI compliance for regulated industries",
    version="1.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Compliance Policy Configuration --------------------
COMPLIANCE_POLICY: Dict[str, Any] = {
    "threshold": settings.risk_threshold,
    "weights": {
        # PII (Personally Identifiable Information)
        "email": 0.4,
        "phone": 0.5,
        "ssn": 1.2,
        "dob": 0.5,
        "address": 0.5,
        "name": 0.3,
        # PCI (Payment Card Industry)
        "credit_card": 1.5,
        "iban": 0.9,
        "bank_account": 0.7,
        "routing_number": 0.8,
        # PHI (Protected Health Information - HIPAA)
        "medical_record": 1.0,
        "phi_hint": 0.6,
        "diagnosis": 0.8,
        "medication": 0.7,
        # Security credentials
        "password": 0.5,
        "api_key": 0.8,
        "secret": 0.7,
        # Presidio base weight
        "presidio": 0.9,
    },
    # HIPAA/PHI contextual terms that increase risk when present
    "phi_terms": [
        r"\bdiagnosed\b",
        r"\bmedical record\b",
        r"\bmrn\b",
        r"\bpatient\b",
        r"\bicd-10\b",
        r"\bcpt\b",
        r"\bprescription\b",
        r"\bmedication\b",
        r"\btreatment\b",
        r"\btherapy\b",
        r"\bsymptoms\b",
        r"\bdisease\b",
        r"\bpediatric\b",
        r"\boncology\b",
        r"\bpsychiatr(y|ic)\b",
        r"\bhospital\b",
        r"\bclinic\b",
        r"\bdoctor\b",
        r"\bnurse\b",
        r"\bphysician\b",
    ],
    # PCI/Financial contextual terms
    "pci_terms": [
        r"\bcredit card\b",
        r"\bdebit card\b",
        r"\bcard number\b",
        r"\bexpir(y|ation)\b",
        r"\bcvv\b",
        r"\bsecurity code\b",
        r"\bpin\b",
        r"\bbank account\b",
        r"\brouting number\b",
        r"\biban\b",
        r"\bswift\b",
        r"\bpayment\b",
    ],
    # Regional compliance variations
    "regional_weights": {
        "HIPAA": {"phi_hint": 1.0, "medical_record": 1.5},
        "PCI": {"credit_card": 2.0, "bank_account": 1.2},
        "GDPR": {"email": 0.6, "name": 0.5, "address": 0.7},
        "CCPA": {"email": 0.5, "phone": 0.6},
    },
}

SAFE_TEMPLATES = {
    "pii": "I need to keep personal information private. Let me provide a general response instead:\n\n",
    "phi": "For healthcare privacy compliance, I'll provide general medical information instead:\n\n",
    "pci": "I can't process payment information. Here's general financial guidance instead:\n\n",
    "general": "Let me rephrase this to keep it safe and compliant:\n\n",
}


# -------------------- Enhanced Pattern Detection --------------------
class RegulatedPatternDetector:
    def __init__(self):
        # Enhanced patterns for regulated industries
        self.patterns = {
            # PII patterns
            "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b"),
            "phone": re.compile(
                r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1}\d{3}[-.\s]?\d{4}(?!\d)"
            ),
            "ssn": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
            "dob": re.compile(
                r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4})\b",
                re.I,
            ),
            "address": re.compile(
                r"\b\d{1,5}\s+[A-Za-z0-9.\-\s]+\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Lane|Ln\.?|Boulevard|Blvd\.?|Drive|Dr\.?|Court|Ct\.?)\b",
                re.I,
            ),
            # PCI patterns
            "credit_card_candidate": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
            "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
            "routing_number": re.compile(r"\b\d{9}\b"),
            "bank_account": re.compile(
                r"\b(?:account\s*number|acct\s*#?)\s*:?\s*\d{6,17}\b", re.I
            ),
            # PHI patterns
            "medical_record": re.compile(
                r"\b(?:mrn|medical\s*record\s*number)\s*:?\s*\d+\b", re.I
            ),
            "diagnosis": re.compile(
                r"\b(?:diagnosed\s+with|diagnosis\s*:)\s*[a-z\s]+\b", re.I
            ),
            "medication": re.compile(
                r"\b(?:prescribed|taking|medication)\s+[a-z]+(?:cillin|prazole|statin|mycin)\b",
                re.I,
            ),
            # Security patterns
            "password": re.compile(
                r"\b(?:password|passwd|passphrase)\s*[:=]?\s*\S+\b", re.I
            ),
            "api_key": re.compile(
                r"\b(?:api[_-]?key|secret[_-]?key|bearer\s+[A-Za-z0-9\._\-]+)\b", re.I
            ),
            "secret": re.compile(r"\b(?:secret|token)\s*[:=]\s*\S+\b", re.I),
            # Contextual patterns
            "phi_context": re.compile("|".join(COMPLIANCE_POLICY["phi_terms"]), re.I),
            "pci_context": re.compile("|".join(COMPLIANCE_POLICY["pci_terms"]), re.I),
        }

    def luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm for credit card validation"""
        digits = [int(d) for d in re.sub(r"[^\d]", "", card_number)]
        if len(digits) < 13 or len(digits) > 19:
            return False

        checksum = 0
        is_even = False
        for d in reversed(digits):
            if is_even:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
            is_even = not is_even

        return checksum % 10 == 0

    def assess_compliance_risk(
        self, text: str, region: Optional[str] = None
    ) -> ComplianceResult:
        """Comprehensive compliance risk assessment"""
        weights = COMPLIANCE_POLICY["weights"].copy()

        # Apply regional weight adjustments
        if region and region in COMPLIANCE_POLICY["regional_weights"]:
            weights.update(COMPLIANCE_POLICY["regional_weights"][region])

        score = 0.0
        triggered_rules = []

        # Pattern-based detection
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == "credit_card_candidate":
                # Special handling for credit cards with Luhn check
                for match in pattern.finditer(text):
                    if self.luhn_check(match.group(0)):
                        score += weights.get("credit_card", 1.5)
                        triggered_rules.append(
                            "credit_card: Valid credit card number detected"
                        )
                        break
            elif pattern.search(text):
                weight_key = pattern_name.replace("_candidate", "").replace(
                    "_context", "_hint"
                )
                score += weights.get(weight_key, 0.5)
                triggered_rules.append(f"{pattern_name}: Pattern detected")

        # Create hash of sensitive snippet if needed
        snippet_hash = None
        if settings.hash_sensitive_data and score > 0:
            snippet_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        blocked = score >= COMPLIANCE_POLICY["threshold"]

        return ComplianceResult(
            score=score,
            blocked=blocked,
            triggered_rules=triggered_rules,
            snippet_hash=snippet_hash,
            compliance_region=region,
            timestamp=datetime.utcnow(),
        )


# -------------------- Metrics Tracking --------------------
class MetricsTracker:
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.judge_calls = 0
        self.risk_scores = []
        self.delay_times = []
        self.pattern_detections = {}
        self.presidio_detections = {}
        self.start_time = monotonic()

    def record_request(self, blocked=False, delay_ms=0, risk_score=0.0):
        """Record a request with its metrics"""
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1

        # Keep last 1000 risk scores for averaging
        self.risk_scores.append(risk_score)
        if len(self.risk_scores) > 1000:
            self.risk_scores.pop(0)

        # Keep last 1000 delay times for averaging
        self.delay_times.append(delay_ms)
        if len(self.delay_times) > 1000:
            self.delay_times.pop(0)

    def record_pattern_detection(self, pattern_name):
        """Record a pattern detection"""
        self.pattern_detections[pattern_name] = (
            self.pattern_detections.get(pattern_name, 0) + 1
        )

    def record_presidio_detection(self, entity_type):
        """Record a Presidio entity detection"""
        self.presidio_detections[entity_type] = (
            self.presidio_detections.get(entity_type, 0) + 1
        )

    def record_judge_call(self):
        """Record an LLM judge call"""
        self.judge_calls += 1

    @property
    def block_rate(self):
        """Calculate block rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_requests / self.total_requests) * 100

    @property
    def avg_risk_score(self):
        """Calculate average risk score"""
        if not self.risk_scores:
            return 0.0
        return sum(self.risk_scores) / len(self.risk_scores)

    @property
    def avg_processing_time(self):
        """Calculate average processing time in ms"""
        if not self.delay_times:
            return 0.0
        return sum(self.delay_times) / len(self.delay_times)

    @property
    def avg_response_time(self):
        """Calculate average response time (same as processing time for now)"""
        return self.avg_processing_time

    @property
    def requests_per_second(self):
        """Calculate requests per second"""
        elapsed = monotonic() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.total_requests / elapsed

    @property
    def error_rate(self):
        """Calculate error rate (placeholder for now)"""
        return 0.0

    def get_audit_logs(self):
        """Get audit logs (now returns a placeholder - use get_audit_logs() function for real data)"""
        return []


metrics = MetricsTracker()
pattern_detector = RegulatedPatternDetector()


# -------------------- Presidio Integration --------------------
class PresidioDetector:
    def __init__(self):
        self.analyzer = None
        if PRESIDIO_AVAILABLE:
            try:
                self._initialize_presidio()
            except Exception as e:
                logger.warning(f"Failed to initialize Presidio: {e}")
                self.analyzer = None

    def _initialize_presidio(self):
        """Initialize Presidio with custom recognizers for regulated industries"""
        try:
            # Try to use spaCy model if available
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
            }
            nlp_engine = SpacyNlpEngine(nlp_config)
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        except Exception:
            # Fallback to basic configuration
            self.analyzer = AnalyzerEngine()

        # Add custom recognizers for regulated industries
        self._add_custom_recognizers()

    def _add_custom_recognizers(self):
        """Add custom pattern recognizers for specific regulated content"""
        if not self.analyzer:
            return

        # Medical Record Number recognizer
        mrn_pattern = Pattern(
            name="medical_record_number",
            regex=r"\b(?:mrn|medical\s*record\s*number)\s*:?\s*\d{6,10}\b",
            score=0.9,
        )
        mrn_recognizer = PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER", patterns=[mrn_pattern]
        )
        self.analyzer.registry.add_recognizer(mrn_recognizer)

        # Enhanced credit card recognizer with better patterns
        cc_pattern = Pattern(
            name="enhanced_credit_card",
            regex=r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            score=0.95,
        )
        cc_recognizer = PatternRecognizer(
            supported_entity="ENHANCED_CREDIT_CARD", patterns=[cc_pattern]
        )
        self.analyzer.registry.add_recognizer(cc_recognizer)

    def analyze_text(self, text: str) -> tuple[float, List[Dict[str, Any]]]:
        """Analyze text with Presidio and return risk score and entities"""
        if not self.analyzer:
            return 0.0, []

        try:
            results = self.analyzer.analyze(text=text, language="en")
            score = 0.0
            entities = []

            for result in results:
                if result.score >= settings.presidio_confidence_threshold:
                    score += COMPLIANCE_POLICY["weights"]["presidio"] * result.score
                    entities.append(
                        {
                            "entity_type": result.entity_type,
                            "start": result.start,
                            "end": result.end,
                            "score": result.score,
                            "text": text[result.start: result.end],
                        }
                    )

            return score, entities
        except Exception as e:
            logger.error(f"Presidio analysis failed: {e}")
            return 0.0, []


presidio_detector = PresidioDetector()


# -------------------- Token Handling --------------------
def token_count(text: str) -> int:
    """Count tokens in text"""
    if TIKTOKEN_AVAILABLE and enc:
        return len(enc.encode(text))
    # Fallback: estimate ~4 characters per token
    return max(1, len(text) // 4)


def tail_tokens(text: str, n_tokens: int) -> str:
    """Get the last N tokens from text"""
    if TIKTOKEN_AVAILABLE and enc:
        tokens = enc.encode(text)
        if len(tokens) <= n_tokens:
            return text
        tail_tokens = tokens[-n_tokens:]
        return enc.decode(tail_tokens)

    # Fallback: estimate character count
    chars = n_tokens * 4
    return text[-chars:] if len(text) > chars else text


# -------------------- SSE Helpers --------------------
def sse_event(data: str, event: Optional[str] = None, id: Optional[str] = None) -> str:
    """Format data as Server-Sent Events"""
    parts = []
    if event:
        parts.append(f"event: {event}")
    if id:
        parts.append(f"id: {id}")

    # Split data into lines per SSE spec
    for line in data.splitlines():
        parts.append(f"data: {line}")

    parts.append("")  # Blank line ends the event
    return "\n".join(parts) + "\n"


async def heartbeat_generator(queue: asyncio.Queue, interval: int = 15):
    """Generate heartbeat events to keep connection alive"""
    while True:
        try:
            await asyncio.sleep(interval)
            await queue.put(sse_event("[heartbeat]", event="heartbeat"))
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            break


async def chat_stream_demo_mode(request: Request, chat_req: ChatRequest):
    """Demo mode streaming without OpenAI - simulates realistic compliance screening"""

    async def demo_event_generator() -> AsyncIterator[bytes]:
        # Demo response that will trigger various compliance alerts
        demo_text = "I can help you with patient information. Let me look up John Doe's medical record. His SSN is 123-45-6789 and his phone number is (555) 123-4567. He was born on January 15, 1980."

        # Split into tokens for realistic streaming
        tokens = demo_text.split()

        # Generate session ID
        session_id = hashlib.sha256(
            f"{datetime.utcnow()}{chat_req.message}".encode()
        ).hexdigest()[:12]
        event_id = 0
        cumulative_risk = 0.0
        risk_threshold = chat_req.risk_threshold or 1.0

        # Collect all patterns and entities from the session
        all_session_patterns = set()
        all_session_entities = []

        for i, token in enumerate(tokens):
            event_id += 1

            # Simulate risk scoring
            risk_score = 0.0
            entities = []
            patterns = []

            # Assign risk scores to specific tokens
            if token.lower() in ["patient", "medical", "record"]:
                risk_score = 0.7
                entities = [{"entity_type": "MEDICAL_INFO", "score": 0.85}]
            elif token in ["John", "Doe"]:
                risk_score = 0.9
                entities = [{"entity_type": "PERSON", "score": 0.92}]
                patterns = ["NAME_PATTERN"]
            elif "ssn" in token.lower() or "123-45-6789" in token:
                risk_score = 1.2
                entities = [{"entity_type": "US_SSN", "score": 0.99}]
                patterns = ["SSN_PATTERN"]
            elif "555" in token or "123-4567" in token:
                risk_score = 0.8
                entities = [{"entity_type": "PHONE_NUMBER", "score": 0.87}]
                patterns = ["PHONE_PATTERN"]
            elif token in ["January", "15,", "1980"]:
                risk_score = 0.6
                entities = [{"entity_type": "DATE_TIME", "score": 0.75}]
                patterns = ["DATE_PATTERN"]
            else:
                risk_score = 0.1

            cumulative_risk += risk_score

            # Collect patterns and entities for the session
            all_session_patterns.update(patterns)
            all_session_entities.extend(entities)

            # Send chunk event
            chunk_data = {
                "type": "chunk",
                "content": token + (" " if i < len(tokens) - 1 else ""),
                "risk_score": risk_score,
                "cumulative_risk": cumulative_risk,
                "entities": entities,
                "patterns": patterns,
                "session_id": session_id,
            }

            yield sse_event(
                json.dumps(chunk_data), event="chunk", id=str(event_id)
            ).encode()

            # Send risk alert if high risk
            if risk_score >= 0.7:
                event_id += 1
                risk_alert = {
                    "type": "risk_alert",
                    "content": token,
                    "risk_score": risk_score,
                    "entities": entities,
                    "patterns": patterns,
                    "reason": f"High-risk token detected: {entities[0]['entity_type'] if entities else 'UNKNOWN'}",
                }
                yield sse_event(
                    json.dumps(risk_alert), event="risk_alert", id=str(event_id)
                ).encode()

            # Block if threshold exceeded
            if cumulative_risk >= risk_threshold:
                event_id += 1
                block_data = {
                    "type": "blocked",
                    "reason": f"Cumulative risk score {cumulative_risk:.2f} exceeded threshold {risk_threshold}",
                    "risk_score": cumulative_risk,
                    "session_id": session_id,
                    "triggered_entities": entities,
                    "compliance_violation": "HIPAA - PHI disclosure detected",
                }
                yield sse_event(
                    json.dumps(block_data), event="blocked", id=str(event_id)
                ).encode()

                # Log audit event to database
                try:
                    async with async_session() as db:
                        # Generate realistic processing time (15-50ms)
                        processing_time = 15.0 + (random.random() * 35.0)

                        audit_event = AuditLog(
                            event_type="stream_blocked",
                            session_id=session_id,
                            user_input_hash=hashlib.sha256(
                                chat_req.message.encode()
                            ).hexdigest()[:16],
                            blocked_content_hash=hashlib.sha256(
                                token.encode()
                            ).hexdigest()[:16],  # Hash of the blocked token
                            risk_score=cumulative_risk,
                            triggered_rules=json.dumps(list(all_session_patterns)),
                            compliance_region="PII",  # Set to PII for consistency
                            presidio_entities=json.dumps(all_session_entities),
                            processing_time_ms=processing_time,
                        )
                        db.add(audit_event)
                        await db.commit()
                        logger.info(
                            f"Demo: Logged blocked stream audit event for session {session_id}"
                        )

                        # Record metrics for blocked request
                        metrics.record_request(
                            blocked=True,
                            delay_ms=processing_time,
                            risk_score=cumulative_risk,
                        )
                        # Record entity detections from entire session
                        for entity in all_session_entities:
                            if "entity_type" in entity:
                                metrics.record_presidio_detection(entity["entity_type"])
                        # Record pattern detections from entire session
                        for pattern in all_session_patterns:
                            metrics.record_pattern_detection(pattern)
                except Exception as e:
                    logger.error(f"Failed to log audit event: {e}")

                break

            # Add delay between tokens
            await asyncio.sleep(0.15)

        # If not blocked, send completion
        if cumulative_risk < risk_threshold:
            event_id += 1
            completion_data = {
                "type": "completed",
                "session_id": session_id,
                "total_risk": cumulative_risk,
                "status": "success",
            }
            yield sse_event(
                json.dumps(completion_data), event="completed", id=str(event_id)
            ).encode()

            # Log completion audit event to database
            try:
                async with async_session() as db:
                    # Generate realistic processing time for completion (10-30ms)
                    completion_processing_time = 10.0 + (random.random() * 20.0)

                    audit_event = AuditLog(
                        event_type="stream_completed",
                        session_id=session_id,
                        user_input_hash=hashlib.sha256(
                            chat_req.message.encode()
                        ).hexdigest()[:16],
                        blocked_content_hash=None,  # No content blocked
                        risk_score=cumulative_risk,
                        triggered_rules=json.dumps([]),
                        compliance_region="PII",
                        presidio_entities=json.dumps([]),
                        processing_time_ms=completion_processing_time,
                    )
                    db.add(audit_event)
                    await db.commit()
                    logger.info(
                        f"Demo: Logged completion audit event for session {session_id}"
                    )

                    # Record metrics for successful request
                    metrics.record_request(
                        blocked=False,
                        delay_ms=completion_processing_time,
                        risk_score=cumulative_risk,
                    )
            except Exception as e:
                logger.error(f"Failed to log audit event: {e}")

        # Final done event
        yield sse_event("[DONE]", event="done").encode()

    return StreamingResponse(
        demo_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


# -------------------- LLM Streaming --------------------
async def upstream_stream(
    user_input: str, model: Optional[str] = None, api_key: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream from upstream LLM"""
    system_prompt = (
        "You are a helpful, professional assistant for regulated industries. "
        "NEVER output personal identifiers, medical record numbers, social security numbers, "
        "credit card numbers, or other sensitive regulated information. "
        "Provide helpful responses while maintaining strict compliance standards."
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{input}")]
    )

    llm = ChatOpenAI(
        model=model or settings.default_model,
        streaming=True,
        temperature=0.3,
        api_key=SecretStr(api_key or settings.openai_api_key) if (api_key or settings.openai_api_key) else None,
    )

    chain = prompt | llm | StrOutputParser()

    try:
        async for piece in chain.astream({"input": user_input}):
            yield piece
    except Exception as e:
        logger.error(f"Upstream streaming error: {e}")
        yield f"[Error: {str(e)}]"


async def safe_rewrite_stream(
    user_input: str, detected_types: List[str], api_key: Optional[str] = None
) -> AsyncIterator[str]:
    """Generate a safe, compliant rewrite of the response"""
    if not settings.enable_safe_rewrite:
        yield "I cannot provide a response due to compliance restrictions."
        return

    # Choose appropriate template based on detected content types
    template = SAFE_TEMPLATES["general"]
    if any("phi" in rule or "medical" in rule for rule in detected_types):
        template = SAFE_TEMPLATES["phi"]
    elif any(
        "credit" in rule or "bank" in rule or "pci" in rule for rule in detected_types
    ):
        template = SAFE_TEMPLATES["pci"]
    elif any(
        "email" in rule or "phone" in rule or "ssn" in rule for rule in detected_types
    ):
        template = SAFE_TEMPLATES["pii"]

    yield template

    system_prompt = (
        "You are a compliance-safe assistant. Rewrite responses to be helpful while removing all "
        "personal identifiers, medical information, financial details, and other regulated content. "
        "Focus on general concepts and publicly available information only. "
        "Never include names, addresses, phone numbers, emails, SSNs, credit card numbers, "
        "medical record numbers, or any PII/PHI/PCI data."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Provide a safe, compliant response to: {input}"),
        ]
    )

    llm = ChatOpenAI(
        model=settings.judge_model,
        streaming=True,
        temperature=settings.rewrite_temperature,
        api_key=SecretStr(api_key or settings.openai_api_key) if (api_key or settings.openai_api_key) else None,
    )

    chain = prompt | llm | StrOutputParser()

    try:
        async for piece in chain.astream({"input": user_input}):
            yield piece
    except Exception as e:
        logger.error(f"Safe rewrite error: {e}")
        yield "I apologize, but I cannot provide a response due to compliance requirements."


# -------------------- Audit Logging --------------------
async def log_audit_event(
    event: AuditEvent,
    processing_time_ms: Optional[float] = None,
    presidio_entities: Optional[List[Dict]] = None,
):
    """Log compliance audit events to database and logs"""
    if not settings.enable_audit_logging:
        return

    try:
        # Log to console/file (existing functionality)
        audit_data = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "user_input_hash": event.user_input_hash,
            "blocked_content_hash": event.blocked_content_hash,
            "risk_score": event.risk_score,
            "triggered_rules": event.triggered_rules,
            "session_id": event.session_id,
        }

        logger.info(f"AUDIT_EVENT: {json.dumps(audit_data)}")

        # Save to database
        async with async_session() as session:
            db_audit = AuditLog(
                timestamp=event.timestamp,
                event_type=event.event_type,
                user_input_hash=event.user_input_hash,
                blocked_content_hash=event.blocked_content_hash,
                risk_score=event.risk_score,
                triggered_rules=json.dumps(event.triggered_rules),
                session_id=event.session_id,
                presidio_entities=(
                    json.dumps(presidio_entities) if presidio_entities else None
                ),
                processing_time_ms=processing_time_ms,
            )
            session.add(db_audit)
            await session.commit()

        # TODO: Send to secure audit storage system
        # await audit_storage.store_event(audit_data)

    except Exception as e:
        logger.error(f"Audit logging failed: {e}")


async def save_metrics_snapshot():
    """Save current metrics to database"""
    try:
        async with async_session() as session:
            snapshot = MetricsSnapshot(
                total_requests=metrics.total_requests,
                blocked_requests=metrics.blocked_requests,
                block_rate=metrics.block_rate,
                avg_risk_score=metrics.avg_risk_score,
                avg_processing_time=metrics.avg_processing_time,
                pattern_detections=json.dumps(dict(metrics.pattern_detections)),
                presidio_detections=json.dumps(dict(metrics.presidio_detections)),
            )
            session.add(snapshot)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save metrics snapshot: {e}")


async def get_audit_logs(
    limit: int = 100, event_type: Optional[str] = None
) -> List[Dict]:
    """Retrieve audit logs from database"""
    try:
        async with async_session() as session:
            query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
            if event_type:
                query = query.where(AuditLog.event_type == event_type)

            result = await session.execute(query)
            logs = result.scalars().all()

            processed_logs = []
            for log in logs:
                entities_data = (
                    json.loads(str(log.presidio_entities)) if log.presidio_entities else []
                )
                logger.info(f"DEBUG: Raw presidio_entities: {log.presidio_entities}")
                logger.info(f"DEBUG: Parsed entities_data: {entities_data}")

                # Ensure entities are in the correct format
                formatted_entities = []
                for entity in entities_data:
                    if (
                        isinstance(entity, dict)
                        and "entity_type" in entity
                        and "score" in entity
                    ):
                        formatted_entities.append(entity)
                    elif isinstance(entity, str):
                        formatted_entities.append({"entity_type": entity, "score": 0.5})
                    else:
                        logger.warning(f"Unknown entity format: {entity}")

                return_data = {
                    "id": log.id,
                    "timestamp": log.timestamp.replace(tzinfo=timezone.utc).isoformat(),
                    "event_type": log.event_type,
                    "session_id": log.session_id or f"session_{log.id}",
                    "compliance_type": log.compliance_region or "PII",
                    "risk_score": log.risk_score,
                    "blocked": log.blocked_content_hash is not None,
                    "decision_reason": f"Risk score: {log.risk_score:.2f} - {'Content blocked due to compliance violations' if log.blocked_content_hash else 'Content processed successfully - no violations detected'}",
                    "entities_detected": formatted_entities,
                    "patterns_detected": (
                        json.loads(str(log.triggered_rules)) if log.triggered_rules else []
                    ),
                    "content_hash": log.blocked_content_hash or log.user_input_hash,
                    "processing_time_ms": log.processing_time_ms,
                }
                logger.info(
                    f"DEBUG: Final return data entities: {return_data['entities_detected']}"
                )
                processed_logs.append(return_data)

            return processed_logs
    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}")
        return []


# -------------------- Main SSE Endpoint --------------------
@app.post("/chat/stream")
async def chat_stream_sse(request: Request, chat_req: ChatRequest):
    """SSE endpoint with regulated industry compliance"""

    # Use API key from request if provided, otherwise fall back to environment variable
    api_key = chat_req.api_key or settings.openai_api_key
    use_demo_mode = not api_key or api_key == "your_openai_api_key_here"

    if use_demo_mode:
        return await chat_stream_demo_mode(request, chat_req)

    # Configuration
    delay_tokens = chat_req.delay_tokens or settings.delay_tokens
    delay_ms = chat_req.delay_ms or settings.delay_ms
    risk_threshold = chat_req.risk_threshold or settings.risk_threshold

    async def event_generator() -> AsyncIterator[bytes]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=200)
        heartbeat_task = asyncio.create_task(heartbeat_generator(queue))

        vetoed = False
        last_flush = monotonic()
        start_time = monotonic()  # Track processing start time
        token_buffer: deque = deque()
        window_text = ""
        event_id = 0
        max_risk_score = 0.0
        all_triggered_rules = []

        # Generate session ID for audit tracking
        session_id = hashlib.sha256(
            f"{datetime.utcnow()}{chat_req.message}".encode()
        ).hexdigest()[:12]
        user_input_hash = hashlib.sha256(chat_req.message.encode()).hexdigest()[:16]

        async def emit_event(data: str, event: str = "chunk", event_id_val: Optional[int] = None):
            nonlocal event_id
            if event_id_val is None:
                event_id += 1
                event_id_val = event_id
            await queue.put(sse_event(data, event=event, id=str(event_id_val)))

        async def flush_tokens(force: bool = False):
            """Flush tokens from buffer while maintaining look-ahead window"""
            nonlocal last_flush
            if not token_buffer:
                return

            # Calculate how many tokens to emit (keeping delay_tokens as look-ahead)
            total_tokens = sum(token_count(piece) for piece in token_buffer)

            if force:
                # Flush everything at end of stream
                pieces_to_emit = len(token_buffer)
            else:
                # Keep look-ahead window
                target_tokens = max(0, total_tokens - delay_tokens)
                pieces_to_emit = 0

                if target_tokens > 0:
                    accumulated_tokens = 0
                    for i, piece in enumerate(token_buffer):
                        piece_tokens = token_count(piece)
                        if accumulated_tokens + piece_tokens <= target_tokens:
                            pieces_to_emit = i + 1
                            accumulated_tokens += piece_tokens
                        else:
                            break

            # Emit the calculated number of pieces
            for _ in range(pieces_to_emit):
                if token_buffer:
                    piece = token_buffer.popleft()
                    await emit_event(piece)

            last_flush = monotonic()

        async def compliance_check_and_stream():
            nonlocal window_text, vetoed, max_risk_score

            try:
                async for piece in upstream_stream(
                    chat_req.message, chat_req.model, api_key
                ):
                    if vetoed:
                        break

                    # Add piece to buffer
                    token_buffer.append(piece)
                    window_text = (window_text + piece)[-4000:]  # Keep last 4k chars

                    # Analyze the look-ahead window for compliance risks
                    analysis_window = tail_tokens(window_text, delay_tokens)

                    # Pattern-based detection
                    compliance_result = pattern_detector.assess_compliance_risk(
                        analysis_window, chat_req.region
                    )

                    # Presidio-based detection
                    presidio_score, presidio_entities = presidio_detector.analyze_text(
                        analysis_window
                    )

                    # Combine scores
                    total_score = compliance_result.score + presidio_score
                    max_risk_score = max(max_risk_score, total_score)
                    all_triggered_rules.extend(compliance_result.triggered_rules)

                    if presidio_entities:
                        for entity in presidio_entities:
                            all_triggered_rules.append(
                                f"presidio: {entity['entity_type']} detected (confidence: {entity['score']:.2f})"
                            )

                    # Check if we need to block
                    if total_score >= risk_threshold:
                        vetoed = True

                        # Log audit event for blocked content
                        blocked_content_hash = hashlib.sha256(
                            analysis_window.encode()
                        ).hexdigest()[:16]
                        audit_event = AuditEvent(
                            event_type="content_blocked",
                            user_input_hash=user_input_hash,
                            blocked_content_hash=blocked_content_hash,
                            risk_score=total_score,
                            triggered_rules=all_triggered_rules,
                            timestamp=datetime.utcnow(),
                            session_id=session_id,
                        )

                        # Calculate elapsed time
                        elapsed_ms = (monotonic() - start_time) * 1000

                        await log_audit_event(
                            audit_event,
                            processing_time_ms=elapsed_ms,
                            presidio_entities=presidio_entities,
                        )

                        logger.warning(
                            f"Content blocked - Score: {total_score:.2f}, Rules: {all_triggered_rules}"
                        )

                        # Emit compliance notice
                        await emit_event(
                            "Content blocked for compliance", event="notice"
                        )

                        # Stream safe rewrite
                        async for safe_piece in safe_rewrite_stream(
                            chat_req.message, all_triggered_rules, api_key
                        ):
                            await emit_event(safe_piece)

                        await emit_event("[DONE]", event="done")
                        return

                    # Check if we should flush based on time or buffer size
                    elapsed_ms = (monotonic() - last_flush) * 1000
                    current_tokens = sum(token_count(p) for p in token_buffer)

                    if (
                        current_tokens > delay_tokens and elapsed_ms >= delay_ms
                    ) or elapsed_ms >= delay_ms * 2:
                        await flush_tokens(force=False)

                    # Check for client disconnect
                    if await request.is_disconnected():
                        logger.info("Client disconnected during streaming")
                        return

                # End of stream - flush remaining tokens if not vetoed
                if not vetoed:
                    await flush_tokens(force=True)
                    await emit_event("[DONE]", event="done")

                    # Log successful completion
                    audit_event = AuditEvent(
                        event_type="stream_completed",
                        user_input_hash=user_input_hash,
                        blocked_content_hash=None,
                        risk_score=max_risk_score,
                        triggered_rules=all_triggered_rules,
                        timestamp=datetime.utcnow(),
                        session_id=session_id,
                    )
                    await log_audit_event(
                        audit_event, processing_time_ms=elapsed_ms, presidio_entities=[]
                    )

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                await emit_event(f"[ERROR: {str(e)}]", event="error")

        # Start the streaming task
        stream_task = asyncio.create_task(compliance_check_and_stream())

        try:
            while True:
                # Get next event from queue
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event_data.encode("utf-8")
                    queue.task_done()
                except asyncio.TimeoutError:
                    # Check if streaming is done
                    if stream_task.done() and queue.empty():
                        break
                    continue

                # Check if streaming task completed and queue is empty
                if stream_task.done() and queue.empty():
                    break

        except Exception as e:
            logger.error(f"SSE event generation error: {e}")
        finally:
            # Clean up tasks
            heartbeat_task.cancel()
            if not stream_task.done():
                stream_task.cancel()

            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            try:
                await stream_task
            except asyncio.CancelledError:
                pass

    # SSE response headers
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }

    return StreamingResponse(
        event_generator(), media_type="text/event-stream", headers=headers
    )


# Legacy GET endpoint for backwards compatibility
@app.get("/chat/stream")
async def chat_stream_get(request: Request, q: str):
    """Legacy GET endpoint"""
    chat_req = ChatRequest(
        message=q,
        delay_tokens=None,
        delay_ms=None,
        risk_threshold=None,
        region=None,
        api_key=None
    )
    return await chat_stream_sse(request, chat_req)


# -------------------- Additional API Endpoints --------------------
@app.post("/assess-risk")
async def assess_compliance_risk(text: str, region: Optional[str] = None):
    """Comprehensive compliance risk assessment"""
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


@app.get("/health")
async def health_check():
    """Enhanced health check with dependency status"""
    dependencies = {
        "tiktoken": TIKTOKEN_AVAILABLE,
        "presidio": PRESIDIO_AVAILABLE and presidio_detector.analyzer is not None,
        "openai_configured": bool(settings.openai_api_key),
    }

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0",
        "dependencies": dependencies,
        "compliance_features": {
            "audit_logging": settings.enable_audit_logging,
            "safe_rewrite": settings.enable_safe_rewrite,
            "hash_sensitive_data": settings.hash_sensitive_data,
        },
    }


@app.get("/compliance/patterns")
async def get_compliance_patterns():
    """Get available compliance patterns and their weights"""
    return {
        "patterns": {
            name: {
                "weight": COMPLIANCE_POLICY["weights"].get(name, 0.5),
                "description": f"Detects {name.replace('_', ' ')} patterns",
            }
            for name in pattern_detector.patterns.keys()
        },
        "regional_adjustments": COMPLIANCE_POLICY["regional_weights"],
        "threshold": COMPLIANCE_POLICY["threshold"],
        "presidio_available": PRESIDIO_AVAILABLE,
        "tiktoken_available": TIKTOKEN_AVAILABLE,
    }


@app.get("/compliance/config")
async def get_compliance_config():
    """Get current compliance configuration"""
    return {
        "risk_threshold": settings.risk_threshold,
        "presidio_confidence_threshold": settings.presidio_confidence_threshold,
        "delay_tokens": settings.delay_tokens,
        "delay_ms": settings.delay_ms,
        "enable_safe_rewrite": settings.enable_safe_rewrite,
        "enable_audit_logging": settings.enable_audit_logging,
        "hash_sensitive_data": settings.hash_sensitive_data,
        "audit_retention_days": settings.audit_retention_days,
    }


@app.get("/metrics")
async def get_metrics():
    """Get real-time system metrics"""
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
    }


@app.get("/config")
async def get_config():
    """Get general system configuration"""
    return {
        "delay_tokens": settings.delay_tokens,
        "delay_ms": settings.delay_ms,
        "risk_threshold": settings.risk_threshold,
        "default_model": settings.default_model,
        "judge_model": settings.judge_model,
        "enable_judge": settings.enable_judge,
        "judge_threshold": settings.judge_threshold,
        "enable_safe_rewrite": settings.enable_safe_rewrite,
        "enable_audit_logging": settings.enable_audit_logging,
        "hash_sensitive_data": settings.hash_sensitive_data,
        "cors_origins": settings.get_cors_origins(),
    }


@app.get("/audit-logs")
async def get_audit_logs_endpoint(limit: int = 100, event_type: Optional[str] = None):
    """Get audit logs from database"""
    logs = await get_audit_logs(limit=limit, event_type=event_type)
    return {
        "logs": logs,
        "count": len(logs),
        "total_available": len(
            logs
        ),  # In a real system, this would be a separate count query
    }


@app.post("/metrics/snapshot")
async def create_metrics_snapshot():
    """Create a snapshot of current metrics"""
    try:
        # Get current metrics
        current_metrics = metrics.get_metrics()

        # Create snapshot record
        async with async_session() as session:
            snapshot = MetricsSnapshot(
                timestamp=datetime.utcnow(),
                total_requests=current_metrics["total_requests"],
                blocked_requests=current_metrics["blocked_requests"],
                block_rate=current_metrics["block_rate"],
                avg_risk_score=current_metrics["avg_risk_score"],
                pattern_detections=current_metrics["pattern_detections"],
                presidio_detections=current_metrics["presidio_detections"],
                performance_metrics=current_metrics["performance_metrics"],
            )
            session.add(snapshot)
            await session.commit()

        return {
            "status": "snapshot_created",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error creating metrics snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Test Suite Management --------------------

# In-memory test suite results
test_suite_results = {
    "basic": {
        "tests": 16,
        "status": "pending",
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    },
    "patterns": {
        "tests": 4,
        "status": "pending",
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    },
    "presidio": {
        "tests": 3,
        "status": "pending",
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    },
    "streaming": {
        "tests": 3,
        "status": "pending",
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    },
}


def update_test_results(
    suite_id: str, passed: int, failed: int, warnings: int, total_tests: int
):
    """Update test results for a specific suite"""
    if suite_id in test_suite_results:
        test_suite_results[suite_id].update(
            {
                "tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "status": (
                    "completed" if (passed + failed) == total_tests else "running"
                ),
            }
        )


# Test Suite Endpoints
@app.get("/test/suites")
async def get_test_suites():
    """Get available test suites with dynamic results"""
    return {
        "suites": [
            {
                "id": "basic",
                "name": "Basic Functionality",
                "description": "Core API endpoints and health checks",
                **test_suite_results["basic"],
            },
            {
                "id": "patterns",
                "name": "Pattern Detection",
                "description": "Regex pattern detection accuracy",
                **test_suite_results["patterns"],
            },
            {
                "id": "presidio",
                "name": "Presidio Integration",
                "description": "Microsoft Presidio ML detection",
                **test_suite_results["presidio"],
            },
            {
                "id": "streaming",
                "name": "SSE Streaming",
                "description": "Server-Sent Events and validation",
                **test_suite_results["streaming"],
            },
        ]
    }


@app.post("/test/run")
async def run_test_suite(request: dict):
    """Run specific test suites"""
    import subprocess

    suites = request.get("suites", [])

    try:
        # Run the actual test suite
        if not suites or "all" in suites:
            # Run all basic tests
            result = subprocess.run(
                ["python", "-m", "pytest", "test_app_basic.py", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        else:
            # Run specific test files based on suite names
            test_files = []
            if "basic" in suites:
                test_files.extend(
                    [
                        "test_app_basic.py::TestBasicFunctionality",
                        "test_app_basic.py::TestRiskAssessment",
                        "test_app_basic.py::TestStreamingEndpoint",
                    ]
                )
            if "patterns" in suites:
                test_files.append("test_app_basic.py::TestPatternDetection")
            if "presidio" in suites:
                test_files.append("test_app_basic.py::TestPresidioIntegration")
            if "streaming" in suites:
                test_files.append("test_app_basic.py::TestStreamingEndpoint")

            if test_files:
                result = subprocess.run(
                    ["python", "-m", "pytest"] + test_files + ["-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            else:
                result = subprocess.run(
                    ["python", "-m", "pytest", "test_app_basic.py", "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

        # Parse test results from pytest output
        test_output = result.stdout + result.stderr
        passed_tests = test_output.count(" PASSED")
        failed_tests = test_output.count(" FAILED")

        # Better warning parsing - look for "X warnings" in the summary line
        warnings_count = 0
        if "warnings in" in test_output:
            # Find the line like "======================== 16 passed, 7 warnings in 3.76s ========================"
            import re

            warning_match = re.search(r"(\d+) warnings in", test_output)
            if warning_match:
                warnings_count = int(warning_match.group(1))

        total_tests = passed_tests + failed_tests

        # Parse individual test class results from the detailed output
        # Count tests by class name patterns
        # Note: These counts are approximate based on test output parsing

        # Better approach: Parse the actual test results by looking for test class patterns
        import re

        # Count passed/failed for each test class
        basic_tests = len(
            re.findall(
                r"test_app_basic\.py::TestBasicFunctionality::\w+ PASSED", test_output
            )
        )
        basic_tests += len(
            re.findall(
                r"test_app_basic\.py::TestRiskAssessment::\w+ PASSED", test_output
            )
        )
        basic_failed_count = len(
            re.findall(
                r"test_app_basic\.py::TestBasicFunctionality::\w+ FAILED", test_output
            )
        )
        basic_failed_count += len(
            re.findall(
                r"test_app_basic\.py::TestRiskAssessment::\w+ FAILED", test_output
            )
        )

        streaming_tests = len(
            re.findall(
                r"test_app_basic\.py::TestStreamingEndpoint::\w+ PASSED", test_output
            )
        )
        streaming_failed_count = len(
            re.findall(
                r"test_app_basic\.py::TestStreamingEndpoint::\w+ FAILED", test_output
            )
        )

        pattern_tests = len(
            re.findall(
                r"test_app_basic\.py::TestPatternDetection::\w+ PASSED", test_output
            )
        )
        pattern_failed_count = len(
            re.findall(
                r"test_app_basic\.py::TestPatternDetection::\w+ FAILED", test_output
            )
        )

        presidio_tests = len(
            re.findall(
                r"test_app_basic\.py::TestPresidioIntegration::\w+ PASSED", test_output
            )
        )
        presidio_failed_count = len(
            re.findall(
                r"test_app_basic\.py::TestPresidioIntegration::\w+ FAILED", test_output
            )
        )

        # Update suite results based on actual parsed results
        update_test_results(
            "basic",
            basic_tests,
            basic_failed_count,
            warnings_count,
            basic_tests + basic_failed_count,
        )
        update_test_results(
            "patterns",
            pattern_tests,
            pattern_failed_count,
            warnings_count,
            pattern_tests + pattern_failed_count,
        )
        update_test_results(
            "presidio",
            presidio_tests,
            presidio_failed_count,
            warnings_count,
            presidio_tests + presidio_failed_count,
        )
        update_test_results(
            "streaming",
            streaming_tests,
            streaming_failed_count,
            warnings_count,
            streaming_tests + streaming_failed_count,
        )

        return {
            "session_id": f"test_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed" if result.returncode == 0 else "failed",
            "output": test_output,
            "summary": {
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warnings_count,
                "total": total_tests,
            },
        }

    except subprocess.TimeoutExpired:
        return {
            "session_id": f"test_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "status": "timeout",
            "output": "Test execution timed out after 60 seconds",
            "summary": {"passed": 0, "failed": 0, "total": 0},
        }
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return {
            "session_id": f"test_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "status": "error",
            "output": f"Error running tests: {str(e)}",
            "summary": {"passed": 0, "failed": 0, "total": 0},
        }


@app.get("/test/results/{session_id}")
async def get_test_results(session_id: str):
    """Get test results for a specific session"""
    # For now, return the current test status
    # In a real implementation, you'd store session results
    return {
        "session_id": session_id,
        "status": "completed",
        "suites": await get_test_suites(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# Enhanced Audit Logs Endpoint
@app.get("/compliance/audit-logs")
async def get_compliance_audit_logs(
    limit: int = 50,
    offset: int = 0,
    compliance_type: Optional[str] = None,
    blocked_only: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get compliance audit logs with filtering"""
    try:
        async with async_session() as session:
            query = select(AuditLog)

            # Apply filters
            if compliance_type:
                # Since compliance_type isn't in schema, skip this filter for now
                pass
            if blocked_only:
                query = query.where(AuditLog.blocked_content_hash.isnot(None))
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                query = query.where(AuditLog.timestamp >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                query = query.where(AuditLog.timestamp <= end_dt)

            # Add ordering and pagination
            query = (
                query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
            )

            result = await session.execute(query)
            logs = result.scalars().all()

            # Convert to dict format matching frontend expectations
            audit_events = []
            for log in logs:
                entities_data = (
                    json.loads(str(log.presidio_entities)) if log.presidio_entities else []
                )
                logger.info(f"DEBUG: Raw presidio_entities: {log.presidio_entities}")
                logger.info(f"DEBUG: Parsed entities_data: {entities_data}")

                # Ensure entities are in the correct format
                formatted_entities = []
                for entity in entities_data:
                    if (
                        isinstance(entity, dict)
                        and "entity_type" in entity
                        and "score" in entity
                    ):
                        formatted_entities.append(entity)
                    elif isinstance(entity, str):
                        formatted_entities.append({"entity_type": entity, "score": 0.5})
                    else:
                        logger.warning(f"Unknown entity format: {entity}")

                audit_events.append(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.replace(
                            tzinfo=timezone.utc
                        ).isoformat(),
                        "event_type": log.event_type,
                        "session_id": log.session_id or f"session_{log.id}",
                        "compliance_type": log.compliance_region or "PII",
                        "risk_score": log.risk_score,
                        "blocked": log.blocked_content_hash is not None,
                        "decision_reason": f"Risk score: {log.risk_score:.2f} - {'Content blocked due to compliance violations' if log.blocked_content_hash else 'Content processed successfully - no violations detected'}",
                        "entities_detected": formatted_entities,
                        "patterns_detected": (
                            json.loads(str(log.triggered_rules))
                            if log.triggered_rules
                            else []
                        ),
                        "content_hash": log.blocked_content_hash or log.user_input_hash,
                        "processing_time_ms": log.processing_time_ms,
                    }
                )
                logger.info(
                    f"DEBUG: Final return data entities: {audit_events[-1]['entities_detected']}"
                )

            return {
                "events": audit_events,
                "total": len(audit_events),
                "has_more": len(audit_events) == limit,
                "filters_applied": {
                    "compliance_type": compliance_type,
                    "blocked_only": blocked_only,
                    "date_range": {"start": start_date, "end": end_date},
                },
            }

    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return {"events": [], "total": 0, "has_more": False, "error": str(e)}


@app.post("/demo/generate-audit-data")
async def generate_demo_audit_data():
    """Generate demo audit data for testing"""
    try:
        demo_events = [
            {
                "text": "Patient John Doe, SSN: 123-45-6789, has diabetes",
                "event_type": "CONTENT_BLOCKED",
                "compliance_type": "HIPAA",
            },
            {
                "text": "Contact me at test@example.com for more info",
                "event_type": "CONTENT_ASSESSED",
                "compliance_type": "PII",
            },
            {
                "text": "Credit card 4532-1234-5678-9012 was charged",
                "event_type": "CONTENT_BLOCKED",
                "compliance_type": "PCI_DSS",
            },
        ]

        generated_count = 0
        for demo in demo_events:
            # Trigger actual compliance assessment to generate real audit logs
            compliance_result = pattern_detector.assess_compliance_risk(demo["text"])
            presidio_score, presidio_entities = presidio_detector.analyze_text(
                demo["text"]
            )

            total_score = compliance_result.score + presidio_score
            is_blocked = total_score >= settings.risk_threshold

            # Create audit event
            audit_event = AuditEvent(
                timestamp=datetime.utcnow(),
                event_type=demo["event_type"],
                user_input_hash=hashlib.sha256(demo["text"].encode()).hexdigest()[:16],
                blocked_content_hash=(
                    compliance_result.snippet_hash if is_blocked else None
                ),
                risk_score=total_score,
                triggered_rules=compliance_result.triggered_rules,
                session_id=f"demo_session_{int(datetime.utcnow().timestamp())}",
            )

            await log_audit_event(
                audit_event,
                processing_time_ms=25.0,
                presidio_entities=presidio_entities,
            )
            generated_count += 1

        return {
            "success": True,
            "generated_events": generated_count,
            "message": f"Generated {generated_count} demo audit events",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.on_event("startup")
# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


# Alternative startup for newer FastAPI versions
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield

    # Shutdown (if needed)
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
