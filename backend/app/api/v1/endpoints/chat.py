"""Chat and streaming endpoints."""

import json
import hashlib
import asyncio
import logging
from collections import deque
from datetime import datetime
from time import monotonic
from typing import AsyncIterator, Any, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import get_valid_api_key, generate_session_id
from app.core.services import get_metrics, get_pattern_detector, get_presidio_detector
from app.schemas.requests import ChatRequest, AuditEvent
from app.services.sliding_window import SlidingWindowAnalyzer
from app.services.openai_service import upstream_stream
from app.utils.sse import sanitize_for_logging
from app.utils.tokens import token_count

router = APIRouter()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


async def log_audit_event_original(
    event,  # AuditEvent object
    processing_time_ms: Optional[float] = None,
    presidio_entities = None,
):
    """Log audit events using original app.py format"""
    try:
        from app.core.database import async_session, AuditLog
        import json
        
        # Save to database using original format
        async with async_session() as session:
            db_audit = AuditLog(
                timestamp=event.timestamp,
                event_type=event.event_type,
                user_input_hash=event.user_input_hash,
                blocked_content_hash=event.blocked_content_hash,
                risk_score=event.risk_score,
                triggered_rules=json.dumps(event.triggered_rules),
                session_id=event.session_id,
                presidio_entities=json.dumps(presidio_entities) if presidio_entities else None,
                processing_time_ms=processing_time_ms,
            )
            session.add(db_audit)
            await session.commit()
            logger.info(f"AUDIT_EVENT: {event.event_type} saved to database")

    except Exception as e:
        logger.error(f"Audit logging failed: {e}")


@router.post("/stream")
@limiter.limit("10/minute")
async def chat_stream_sse(request: Request, chat_req: ChatRequest):
    """SSE endpoint with regulated industry compliance."""
    
    # Get shared service instances (same as original app.py)
    pattern_detector = get_pattern_detector()
    presidio_detector = get_presidio_detector()
    metrics = get_metrics()
    
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
    
    # If user input violates compliance, block immediately
    if user_total_score >= risk_threshold:
        logger.warning(f"User input blocked - Score: {user_total_score:.2f}, Message: {sanitize_for_logging(chat_req.message)}...")
        
        # Generate hashes for audit logging
        user_input_hash = hashlib.md5(chat_req.message.encode()).hexdigest()
        session_id = generate_session_id()
        
        # Create audit event using original format
        try:
            audit_event = AuditEvent(
                event_type="user_input_blocked",
                user_input_hash=user_input_hash,
                blocked_content_hash=user_input_hash,
                risk_score=user_total_score,
                triggered_rules=user_compliance_result.triggered_rules + ([f"presidio: score {user_presidio_score:.2f}"] if user_presidio_score > 0 else []),
                timestamp=datetime.utcnow(),
                session_id=session_id
            )
            
            await log_audit_event_original(audit_event, 0.0, user_presidio_entities)
            logger.info(f"Audit event logged for blocked content: {user_input_hash}")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        
        # Record metrics for blocked request
        metrics.record_request(
            blocked=True, delay_ms=0, risk_score=user_total_score
        )
        
        # Record pattern detections for metrics
        for rule in user_compliance_result.triggered_rules:
            pattern_name = rule.split(":")[0].strip()
            metrics.record_pattern_detection(pattern_name)
        
        # Return blocking response
        error_message = f"Request blocked due to compliance policy violation (risk score: {user_total_score:.2f})"
        
        async def blocked_response():
            yield f"data: {json.dumps({'type': 'blocked', 'content': error_message, 'risk_score': user_total_score})}\n\n"
        
        return StreamingResponse(
            blocked_response(),
            media_type="text/event-stream"
        )

    # Log successful request audit event
    user_input_hash = hashlib.md5(chat_req.message.encode()).hexdigest()
    session_id = generate_session_id()
    
    # Log audit event using the original format
    try:
        audit_event = AuditEvent(
            event_type="text_analysis",
            user_input_hash=user_input_hash,
            blocked_content_hash=None,
            risk_score=user_total_score,
            triggered_rules=user_compliance_result.triggered_rules + ([f"presidio: score {user_presidio_score:.2f}"] if user_presidio_score > 0 else []),
            timestamp=datetime.utcnow(),
            session_id=session_id
        )
        
        # Use original-style audit logging
        await log_audit_event_original(audit_event, 100.0, user_presidio_entities)
        logger.info(f"Audit event logged for processed content: {user_input_hash}")
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

    # Create proper streaming response using queue-based architecture (like original)
    async def event_generator():
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=200)
        
        # Generate heartbeat to keep connection alive
        async def heartbeat_generator(queue: asyncio.Queue, interval: int = 15):
            while True:
                try:
                    await asyncio.sleep(interval)
                    await queue.put(f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    break
        
        heartbeat_task = asyncio.create_task(heartbeat_generator(queue))
        
        vetoed = False
        token_buffer: deque = deque()
        event_id = 0
        
        async def emit_event(data: str, event: str = "chunk", event_id_val: Optional[int] = None, risk_score: Optional[float] = None):
            nonlocal event_id
            if event_id_val is None:
                event_id += 1
                event_id_val = event_id
            
            event_data = {
                "type": event,
                "content": data,
                "timestamp": datetime.utcnow().isoformat(),
                "risk_score": risk_score
            }
            await queue.put(f"data: {json.dumps(event_data)}\n\n")
        
        async def flush_tokens(force: bool = False):
            """Flush tokens from buffer while maintaining look-ahead window"""
            if not token_buffer:
                return

            total_tokens = sum(token_count(piece) for piece in token_buffer)
            
            if force:
                pieces_to_emit = len(token_buffer)
            else:
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
            
            for _ in range(pieces_to_emit):
                if token_buffer:
                    piece = token_buffer.popleft()
                    await emit_event(piece, event="chunk")

        try:
            # Stream from OpenAI with proper buffering
            async for piece in upstream_stream(chat_req.message, chat_req.model, chat_req.api_key):
                if vetoed:
                    break
                
                token_buffer.append(piece)
                await flush_tokens()
                await asyncio.sleep(delay_ms / 1000.0)
            
            # Flush remaining tokens
            if not vetoed:
                await flush_tokens(force=True)
                await emit_event("Stream completed successfully", event="completed")
            
            # Process queued events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield event.encode()
                except asyncio.TimeoutError:
                    if queue.empty():
                        break
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            await emit_event(f"Stream error: {str(e)}", event="error")
        
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/stream")
async def chat_stream_get(request: Request, q: str):
    """Legacy GET endpoint for chat stream."""
    chat_req = ChatRequest(
        message=q,
        delay_tokens=None,
        delay_ms=None,
        risk_threshold=None,
        region=None,
        api_key=None
    )
    return await chat_stream_sse(request, chat_req)