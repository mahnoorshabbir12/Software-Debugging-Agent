import os
from tiktoken import get_encoding

# Token utilities for LLM prompt size management
# Use a generic encoding that works for most models (e.g., cl100k_base). This avoids model-specific mapping issues.
_ENCODING = get_encoding("cl100k_base")

def token_count(text: str) -> int:
    """Return the number of tokens in `text` using the selected encoding."""
    return len(_ENCODING.encode(text))

def truncate_to_budget(text: str, max_tokens: int, suffix: str = "...") -> str:
    """Trim `text` so its token count does not exceed `max_tokens`."""
    tokens = _ENCODING.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _ENCODING.decode(tokens[:max_tokens]) + suffix
