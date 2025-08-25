"""Server-Sent Events utilities."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sse_event(data: str, event: Optional[str] = None, id: Optional[str] = None) -> str:
    """Format data as Server-Sent Events."""
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
    """Generate heartbeat events to keep connection alive."""
    while True:
        try:
            await asyncio.sleep(interval)
            await queue.put(sse_event("[heartbeat]", event="heartbeat"))
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            break


def sanitize_for_logging(text: str, max_length: int = 50) -> str:
    """Sanitize text for safe logging without exposing PII."""
    import re
    
    if not text:
        return ""
    # Truncate and mask potential sensitive data
    truncated = text[:max_length]
    # Replace potential SSN, credit card patterns with asterisks for logging
    sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****', truncated)
    sanitized = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '****-****-****-****', sanitized)
    return sanitized
