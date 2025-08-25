"""Token counting and manipulation utilities."""

import logging

logger = logging.getLogger(__name__)

# Check if tiktoken is available
try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    TIKTOKEN_AVAILABLE = True
except ImportError:
    enc = None
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available. Install with: pip install tiktoken")


def token_count(text: str) -> int:
    """Count tokens in text."""
    if TIKTOKEN_AVAILABLE and enc:
        return len(enc.encode(text))
    # Fallback: estimate ~4 characters per token
    return max(1, len(text) // 4)


def tail_tokens(text: str, n_tokens: int) -> str:
    """Get the last N tokens from text."""
    if TIKTOKEN_AVAILABLE and enc:
        tokens = enc.encode(text)
        if len(tokens) <= n_tokens:
            return text
        tail_tokens = tokens[-n_tokens:]
        return enc.decode(tail_tokens)

    # Fallback: estimate character count
    chars = n_tokens * 4
    return text[-chars:] if len(text) > chars else text


def encode_text(text: str) -> list:
    """Encode text to tokens."""
    if TIKTOKEN_AVAILABLE and enc:
        return enc.encode(text)
    # Fallback: split by approximate tokens
    return text.split()


def decode_tokens(tokens: list) -> str:
    """Decode tokens back to text."""
    if TIKTOKEN_AVAILABLE and enc and isinstance(tokens[0], int):
        return enc.decode(tokens)
    # Fallback: join as strings
    return " ".join(str(token) for token in tokens)
