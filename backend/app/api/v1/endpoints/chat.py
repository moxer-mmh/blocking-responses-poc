"""Chat and streaming endpoints."""

import json
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import AsyncIterator, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import get_valid_api_key, generate_session_id
from app.schemas.requests import ChatRequest, AuditEvent
from app.services.compliance import RegulatedPatternDetector
from app.services.presidio_service import PresidioDetector
from app.services.sliding_window import SlidingWindowAnalyzer
from app.services.metrics import MetricsTracker
from app.utils.sse import sse_event, sanitize_for_logging
from app.utils.tokens import token_count

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services (these would ideally be dependency injected)
pattern_detector = RegulatedPatternDetector()
presidio_detector = PresidioDetector()
metrics = MetricsTracker()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/stream")
@limiter.limit("10/minute")
async def chat_stream_sse(request: Request, chat_req: ChatRequest):
    """SSE endpoint with regulated industry compliance."""
    
    # Validate API key
    api_key = get_valid_api_key(chat_req.api_key)
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key is required. Please provide it in the request or set a valid key in the .env file"
        )

    # Configuration
    delay_tokens = chat_req.delay_tokens or settings.delay_tokens
    delay_ms = chat_req.delay_ms or settings.delay_ms
    risk_threshold = chat_req.risk_threshold or settings.risk_threshold

    # Check user input for compliance violations BEFORE streaming
    user_compliance_result = pattern_detector.assess_compliance_risk(
        chat_req.message, chat_req.region
    )
    user_presidio_score, user_presidio_entities = presidio_detector.analyze_text(
        chat_req.message
    )
    user_total_score = user_compliance_result.score + user_presidio_score
    
    # Perform comprehensive sliding window analysis on user input
    input_analyzer = SlidingWindowAnalyzer()
    input_window_analyses = []
    
    # Analyze user input with sliding windows
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        input_tokens = enc.encode(chat_req.message)
        total_input_tokens = len(input_tokens)
        
        # Generate comprehensive window analyses for the input
        position = input_analyzer.frequency
        while position <= total_input_tokens:
            window_text, window_start, window_end = input_analyzer.extract_analysis_window(
                chat_req.message, position
            )
            
            if window_text.strip():  # Only analyze non-empty windows
                window_analysis = input_analyzer.analyze_window(
                    window_text, window_start, window_end, chat_req.region,
                    pattern_detector, presidio_detector
                )
                window_analysis["analysis_position"] = position
                input_window_analyses.append(window_analysis)
            
            position += input_analyzer.frequency
            
        # Ensure we analyze the entire input by adding a final window if needed
        if total_input_tokens > 0 and (not input_window_analyses or input_window_analyses[-1]["window_end"] < total_input_tokens):
            window_text, window_start, window_end = input_analyzer.extract_analysis_window(
                chat_req.message, total_input_tokens
            )
            if window_text.strip():
                window_analysis = input_analyzer.analyze_window(
                    window_text, window_start, window_end, chat_req.region,
                    pattern_detector, presidio_detector
                )
                window_analysis["analysis_position"] = total_input_tokens
                input_window_analyses.append(window_analysis)
                
    except ImportError:
        # Fallback for when tiktoken is not available
        words = chat_req.message.split()
        chunk_size = 25  # Approximate tokens per window
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                # Simple analysis using pattern and presidio detectors directly
                compliance_result = pattern_detector.assess_compliance_risk(chunk_text, chat_req.region)
                presidio_score, presidio_entities = presidio_detector.analyze_text(chunk_text)
                
                window_analysis = {
                    "window_text": chunk_text,
                    "window_start": i,
                    "window_end": min(i + chunk_size, len(words)),
                    "window_size": len(chunk_words),
                    "pattern_score": compliance_result.score,
                    "presidio_score": presidio_score,
                    "total_score": compliance_result.score + presidio_score,
                    "triggered_rules": compliance_result.triggered_rules,
                    "presidio_entities": presidio_entities,
                    "blocked": compliance_result.score + presidio_score >= settings.risk_threshold,
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_position": i + chunk_size
                }
                input_window_analyses.append(window_analysis)
    
    # If user input violates compliance, block immediately
    if user_total_score >= risk_threshold:
        logger.warning(f"User input blocked - Score: {user_total_score:.2f}, Message: {sanitize_for_logging(chat_req.message)}...")
        
        # Record metrics for blocked request
        metrics.record_request(
            blocked=True, delay_ms=0, risk_score=user_total_score
        )
        
        # Record pattern detections for metrics
        for rule in user_compliance_result.triggered_rules:
            pattern_name = rule.split(":")[0].strip()
            metrics.record_pattern_detection(pattern_name)
        
        # Record Presidio detections for metrics
        for entity in user_presidio_entities:
            metrics.record_presidio_detection(entity.get("entity_type", "unknown"))
        
        # Return blocking response
        error_message = f"Request blocked due to compliance policy violation (risk score: {user_total_score:.2f})"
        
        async def blocked_response():
            yield f"data: {json.dumps({'type': 'blocked', 'content': error_message, 'risk_score': user_total_score})}\\n\\n"
        
        return StreamingResponse(
            blocked_response(),
            media_type="text/event-stream"
        )

    # Continue with normal streaming (placeholder for now)
    # This would include the full OpenAI streaming logic from the original
    async def demo_response():
        yield f"data: {json.dumps({'type': 'message', 'content': 'Demo response - OpenAI streaming not yet migrated'})}\\n\\n"
        yield f"data: {json.dumps({'type': 'analysis', 'window_analyses': input_window_analyses})}\\n\\n"
        yield "data: [DONE]\\n\\n"
    
    return StreamingResponse(
        demo_response(),
        media_type="text/event-stream"
    )


@router.get("/stream")
async def chat_stream_get():
    """GET endpoint for chat stream (informational)."""
    return {
        "message": "Chat streaming endpoint",
        "usage": "POST to /chat/stream with ChatRequest body",
        "features": ["Real-time compliance filtering", "SSE streaming", "Window analysis"]
    }
