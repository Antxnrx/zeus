"""
Centralised LLM factory with round-robin Groq API key rotation.

Usage:
    from app.llm import get_llm
    llm = get_llm()                      # uses default temp
    llm = get_llm(temperature=0.0)       # override temp
"""
from __future__ import annotations

import itertools
import logging
import threading

from langchain_groq import ChatGroq

from app.config import GROQ_API_KEYS, GROQ_MODEL, GROQ_TEMPERATURE

logger = logging.getLogger("rift.llm")

# ── Thread-safe round-robin key iterator ────────────────────

_lock = threading.Lock()
_cycle: itertools.cycle[str] | None = None


def _next_key() -> str:
    """Return the next API key in round-robin order (thread-safe)."""
    global _cycle
    with _lock:
        if _cycle is None:
            if not GROQ_API_KEYS:
                raise RuntimeError(
                    "No Groq API keys configured. "
                    "Set GROQ_API_KEYS as a comma-separated list in .env"
                )
            _cycle = itertools.cycle(GROQ_API_KEYS)
            logger.info("Initialised Groq key rotator with %d keys", len(GROQ_API_KEYS))
        return next(_cycle)


# ── Public factory ──────────────────────────────────────────

def get_llm(
    *,
    temperature: float | None = None,
    model: str | None = None,
) -> ChatGroq:
    """
    Return a ChatGroq instance using the next key from the round-robin pool.

    Every call rotates to the next key, spreading requests evenly across keys.
    """
    key = _next_key()
    return ChatGroq(
        model=model or GROQ_MODEL,
        temperature=temperature if temperature is not None else GROQ_TEMPERATURE,
        api_key=key,
    )


def has_llm_keys() -> bool:
    """Return True if at least one Groq API key is configured."""
    return bool(GROQ_API_KEYS)
