"""OpenAI streaming service - migrated from app.py."""

import logging
from typing import AsyncIterator, Optional, List
from pydantic import SecretStr

from app.core.config import settings
from app.core.security import get_valid_api_key

logger = logging.getLogger(__name__)

# Check if LangChain is available
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. Install with: pip install langchain-openai langchain-core")


# Safe rewrite templates
SAFE_TEMPLATES = {
    "pii": "I need to keep personal information private. Let me provide a general response instead:\n\n",
    "phi": "For healthcare privacy compliance, I'll provide general medical information instead:\n\n",
    "pci": "I can't process payment information. Here's general financial guidance instead:\n\n",
    "general": "Let me rephrase this to keep it safe and compliant:\n\n",
}


async def upstream_stream(
    user_input: str, model: Optional[str] = None, api_key: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream from upstream LLM."""
    if not LANGCHAIN_AVAILABLE:
        yield "[Error: LangChain not available for OpenAI streaming]"
        return
        
    valid_api_key = get_valid_api_key(api_key)
    if not valid_api_key:
        yield "[Error: OpenAI API key not available]"
        return
    
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
        api_key=SecretStr(valid_api_key),
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
    """Generate a safe, compliant rewrite of the response."""
    if not settings.enable_safe_rewrite:
        yield "I cannot provide a response due to compliance restrictions."
        return

    if not LANGCHAIN_AVAILABLE:
        yield "I cannot provide a response due to missing dependencies."
        return
        
    valid_api_key = get_valid_api_key(api_key)
    if not valid_api_key:
        yield "I cannot provide a response due to missing API configuration."
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
        api_key=SecretStr(valid_api_key),
    )

    chain = prompt | llm | StrOutputParser()

    try:
        async for piece in chain.astream({"input": user_input}):
            yield piece
    except Exception as e:
        logger.error(f"Safe rewrite error: {e}")
        yield f"[Error: {str(e)}]"
