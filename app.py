# pip install fastapi uvicorn langchain-openai langchain-core pydantic-settings
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from time import monotonic
from collections import deque
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import asyncio, re, logging, json, os
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configuration
class Settings(BaseSettings):
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    default_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    log_level: str = "INFO"
    delay_tokens: int = 20
    delay_ms: int = 250
    risk_threshold: float = 1.0
    judge_threshold: float = 0.8
    enable_judge: bool = True
    cors_origins: str = "*"
    
    class Config:
        env_file = ".env"
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()

# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("blocking_responses")

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    delay_tokens: Optional[int] = Field(None, ge=1, le=100)
    delay_ms: Optional[int] = Field(None, ge=50, le=2000)
    risk_threshold: Optional[float] = Field(None, ge=0.0, le=5.0)

class RiskAssessment(BaseModel):
    score: float
    triggered_rules: List[str]
    snippet: str
    blocked: bool

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"

# Metrics tracking
class Metrics:
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.judge_calls = 0
        self.avg_delay_ms = 0.0
        self.risk_scores = []
    
    def record_request(self, blocked: bool = False, delay_ms: float = 0, risk_score: float = 0):
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1
        self.avg_delay_ms = (self.avg_delay_ms * (self.total_requests - 1) + delay_ms) / self.total_requests
        self.risk_scores.append(risk_score)
        if len(self.risk_scores) > 1000:  # Keep last 1000 scores
            self.risk_scores.pop(0)
    
    def record_judge_call(self):
        self.judge_calls += 1
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.blocked_requests / max(1, self.total_requests),
            "judge_calls": self.judge_calls,
            "avg_delay_ms": round(self.avg_delay_ms, 2),
            "avg_risk_score": round(sum(self.risk_scores) / max(1, len(self.risk_scores)), 3)
        }

metrics = Metrics()

# FastAPI app
app = FastAPI(
    title="Blocking Responses API",
    description="Real-time content filtering for LLM streaming responses",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Risk assessment patterns and rules
class RiskPatterns:
    def __init__(self):
        self.patterns = {
            "email": {
                "regex": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b"),
                "score": 0.5,
                "description": "Email address detected"
            },
            "ssn": {
                "regex": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
                "score": 1.0,
                "description": "SSN pattern detected"
            },
            "credit_card": {
                "regex": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
                "score": 1.0,
                "description": "Credit card pattern detected"
            },
            "phone": {
                "regex": re.compile(r"\b\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b"),
                "score": 0.3,
                "description": "Phone number detected"
            },
            "secrets": {
                "regex": re.compile(r"\b(secret|password|api[_-]?key|token|bearer)\b", re.I),
                "score": 0.8,
                "description": "Potential secret/credential detected"
            },
            "harmful_content": {
                "regex": re.compile(r"\b(kill|murder|suicide|bomb|terrorist)\b", re.I),
                "score": 1.5,
                "description": "Potentially harmful content detected"
            }
        }
    
    def assess_risk(self, text: str) -> RiskAssessment:
        total_score = 0.0
        triggered_rules = []
        
        for rule_name, rule_config in self.patterns.items():
            if rule_config["regex"].search(text):
                total_score += rule_config["score"]
                triggered_rules.append(f"{rule_name}: {rule_config['description']}")
        
        return RiskAssessment(
            score=total_score,
            triggered_rules=triggered_rules,
            snippet=text[:100] + "..." if len(text) > 100 else text,
            blocked=total_score >= settings.risk_threshold
        )

risk_patterns = RiskPatterns()

# LLM Judge for complex risk assessment
class LLMJudge:
    def __init__(self):
        if not settings.openai_api_key:
            logger.warning("No OpenAI API key provided, LLM judge will be disabled")
            self.enabled = False
        else:
            self.enabled = settings.enable_judge
            self.llm = ChatOpenAI(
                model=settings.judge_model,
                temperature=0.0,
                max_tokens=50,
                api_key=settings.openai_api_key
            )
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", 
                 "You are a content safety judge. Analyze the given text snippet and determine if it contains:\n"
                 "- Personal identifiable information (PII)\n"
                 "- Sensitive credentials or secrets\n"
                 "- Harmful, violent, or inappropriate content\n"
                 "- Privacy violations\n\n"
                 "Respond with only 'RISKY' or 'SAFE'. Be conservative - when in doubt, respond 'RISKY'."),
                ("human", "Text snippet: {snippet}")
            ])
            self.chain = self.prompt | self.llm | StrOutputParser()
    
    async def is_risky(self, snippet: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            metrics.record_judge_call()
            start_time = monotonic()
            
            result = await self.chain.ainvoke({"snippet": snippet})
            judgment = result.strip().upper()
            
            elapsed_ms = (monotonic() - start_time) * 1000
            logger.debug(f"Judge call took {elapsed_ms:.1f}ms, result: {judgment}")
            
            return judgment == "RISKY"
        except Exception as e:
            logger.error(f"LLM judge error: {e}")
            return True  # Fail safe - assume risky if error

llm_judge = LLMJudge()

# Safe response templates
SAFE_TEMPLATES = {
    "pii": "I notice this response might contain personal information. Let me provide a general answer instead: ",
    "credentials": "I can't share information that might contain credentials or secrets. Here's a safer approach: ",
    "harmful": "I can't provide that type of content. Let me offer helpful information instead: ",
    "general": "Let me rephrase to keep this safe and compliant: "
}

def get_safe_template(triggered_rules: List[str]) -> str:
    if any("email" in rule or "ssn" in rule or "phone" in rule for rule in triggered_rules):
        return SAFE_TEMPLATES["pii"]
    elif any("secret" in rule for rule in triggered_rules):
        return SAFE_TEMPLATES["credentials"]
    elif any("harmful" in rule for rule in triggered_rules):
        return SAFE_TEMPLATES["harmful"]
    else:
        return SAFE_TEMPLATES["general"]

# Dependency for getting settings
def get_stream_config(req: ChatRequest) -> Dict[str, Any]:
    return {
        "delay_tokens": req.delay_tokens or settings.delay_tokens,
        "delay_ms": req.delay_ms or settings.delay_ms,
        "risk_threshold": req.risk_threshold or settings.risk_threshold,
        "model": req.model or settings.default_model,
        "system_prompt": req.system_prompt or "You are a helpful, concise assistant."
    }

@app.post("/chat/stream")
async def chat_stream(request: Request, chat_req: ChatRequest):
    """Stream chat response with real-time content filtering"""
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    config = get_stream_config(chat_req)
    start_time = monotonic()

    # Build LangChain stream
    prompt = ChatPromptTemplate.from_messages([
        ("system", config["system_prompt"]),
        ("human", "{input}")
    ])
    llm = ChatOpenAI(
        model=config["model"], 
        streaming=True,
        api_key=settings.openai_api_key
    )
    chain = prompt | llm | StrOutputParser()

    async def source():
        try:
            async for chunk in chain.astream({"input": chat_req.message}):
                yield chunk
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield f"Error: {str(e)}"

    async def guarded_stream():
        delay_tokens = config["delay_tokens"]
        delay_ms = config["delay_ms"]
        threshold = config["risk_threshold"]

        buf = deque()
        last_flush = monotonic()
        vetoed = False
        max_risk_score = 0.0
        all_triggered_rules = []

        try:
            async for piece in source():
                # 1) Accumulate
                buf.append(piece)

                # 2) Run fast checks on sliding window
                window_text = "".join(list(buf)[-delay_tokens:])
                risk_assessment = risk_patterns.assess_risk(window_text)
                max_risk_score = max(max_risk_score, risk_assessment.score)
                all_triggered_rules.extend(risk_assessment.triggered_rules)
                
                # 3) Escalate to LLM judge if needed
                if risk_assessment.score >= settings.judge_threshold and llm_judge.enabled:
                    if await llm_judge.is_risky(window_text):
                        risk_assessment.score = max(risk_assessment.score, threshold + 0.1)
                        all_triggered_rules.append("llm_judge: LLM judge flagged content as risky")

                # 4) Check if we should block
                if risk_assessment.score >= threshold:
                    vetoed = True
                    logger.warning(f"Blocking response. Risk: {risk_assessment.score:.2f}, Rules: {risk_assessment.triggered_rules}")
                    
                    safe_template = get_safe_template(all_triggered_rules)
                    yield f"data: {safe_template}\n\n"
                    yield "data: I understand you're looking for information, but I need to be careful about sharing certain types of content. Is there a different way I can help you?\n\n"
                    yield "data: [BLOCKED]\n\n"
                    
                    # Record metrics
                    elapsed_ms = (monotonic() - start_time) * 1000
                    metrics.record_request(blocked=True, delay_ms=elapsed_ms, risk_score=max_risk_score)
                    return

                # 5) Release tokens with look-ahead or time-based flush
                enough_lookahead = len(buf) > delay_tokens
                enough_time = (monotonic() - last_flush) * 1000 >= delay_ms

                if enough_lookahead or enough_time:
                    emit_count = max(0, len(buf) - delay_tokens)
                    for _ in range(emit_count):
                        if buf:
                            tok = buf.popleft()
                            yield f"data: {tok}\n\n"
                    last_flush = monotonic()

                # 6) Check for client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected")
                    return

            # 7) End of stream: flush remaining tokens if not vetoed
            if not vetoed:
                while buf:
                    yield f"data: {buf.popleft()}\n\n"
                yield "data: [DONE]\n\n"
                
                # Record successful completion
                elapsed_ms = (monotonic() - start_time) * 1000
                metrics.record_request(blocked=False, delay_ms=elapsed_ms, risk_score=max_risk_score)
                logger.info(f"Request completed successfully. Max risk: {max_risk_score:.2f}, Duration: {elapsed_ms:.1f}ms")
        
        except Exception as e:
            logger.error(f"Error in guarded stream: {e}")
            yield f"data: Error occurred while processing request\n\n"
            yield "data: [ERROR]\n\n"

    return StreamingResponse(guarded_stream(), media_type="text/event-stream")

# Legacy GET endpoint for backwards compatibility
@app.get("/chat/stream")
async def chat_stream_get(request: Request, q: str):
    """Legacy GET endpoint for chat streaming"""
    chat_req = ChatRequest(message=q)
    return await chat_stream(request, chat_req)

# Risk assessment endpoint
@app.post("/assess-risk")
async def assess_risk_endpoint(text: str):
    """Assess risk of given text without streaming"""
    risk_assessment = risk_patterns.assess_risk(text)
    
    # Also check with LLM judge if score is high enough
    if risk_assessment.score >= settings.judge_threshold and llm_judge.enabled:
        llm_risky = await llm_judge.is_risky(text)
        if llm_risky:
            risk_assessment.triggered_rules.append("llm_judge: LLM judge flagged content as risky")
            risk_assessment.score = max(risk_assessment.score, settings.risk_threshold + 0.1)
            risk_assessment.blocked = True
    
    return risk_assessment

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now()
    )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    stats = metrics.get_stats()
    stats["settings"] = {
        "delay_tokens": settings.delay_tokens,
        "delay_ms": settings.delay_ms,
        "risk_threshold": settings.risk_threshold,
        "judge_enabled": llm_judge.enabled,
        "judge_threshold": settings.judge_threshold
    }
    return stats

# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "delay_tokens": settings.delay_tokens,
        "delay_ms": settings.delay_ms,
        "risk_threshold": settings.risk_threshold,
        "judge_threshold": settings.judge_threshold,
        "judge_enabled": llm_judge.enabled,
        "default_model": settings.default_model,
        "judge_model": settings.judge_model
    }

# Patterns endpoint
@app.get("/patterns")
async def get_patterns():
    """Get current risk patterns"""
    patterns_info = {}
    for name, config in risk_patterns.patterns.items():
        patterns_info[name] = {
            "score": config["score"],
            "description": config["description"],
            "pattern": config["regex"].pattern
        }
    return patterns_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)