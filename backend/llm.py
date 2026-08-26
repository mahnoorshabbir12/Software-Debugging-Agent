"""
Shared LLM factory + traced run config.

Concept: a factory / single construction point
----------------------------------------------
Before Module 21, each agent (triage, hypothesis, evidence, patch) built its own
ChatOpenAI pointed at OpenRouter, duplicating the base_url, api_key and provider
wiring four times. That is four places to edit for any cross-cutting concern.

This factory centralizes construction so provider config (OpenRouter base URL,
API key) lives in ONE place, and optional LangSmith tracing is toggled here.

Concept: attach tracing via run config, not construction
--------------------------------------------------------
We attach the tracer through the *run config* at each `.invoke()` (via
`traced_config()`) rather than binding it to the model object. Why:

  - Passing callbacks in the top-level config makes LangChain/LangGraph
    propagate them down the whole run tree, so we capture the LLM call, any
    tools the graph runs, and node transitions — all from one attach point.
  - Binding callbacks to the model object AND passing them in config would fire
    the handler twice for the same LLM run (duplicate spans). Config-only keeps
    exactly one attach point per run.

Where it's used: triage.py, hypothesis.py, evidence.py, patch.py call
build_llm(...) for construction and pass traced_config(...) when invoking.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from backend.observability.callbacks import TracingCallbackHandler
from backend.observability.config import get_observability_settings
from backend.observability.logging import get_logger

log = get_logger("llm.factory")

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# One shared tracer instance so every run in the process funnels spans through
# the same handler (its per-run state is keyed by run_id, so sharing is safe).
_TRACER: Optional[TracingCallbackHandler] = None


def get_tracer() -> TracingCallbackHandler:
    """Return the process-wide tracing callback handler (created on first use)."""
    global _TRACER
    if _TRACER is None:
        _TRACER = TracingCallbackHandler()
        _maybe_enable_langsmith()
    return _TRACER


def get_tracing_callbacks() -> list:
    """Return the active callback list (empty when observability is disabled)."""
    if not get_observability_settings().enabled:
        return []
    return [get_tracer()]


def traced_config(config: Optional[dict] = None, **configurable: Any) -> dict:
    """
    Merge tracing callbacks (and any `configurable` keys such as thread_id) into
    a LangChain/LangGraph run config. Pass the result as `config=` to .invoke().
    """
    cfg: dict[str, Any] = dict(config or {})

    existing = list(cfg.get("callbacks") or [])
    for cb in get_tracing_callbacks():
        if cb not in existing:
            existing.append(cb)
    if existing:
        cfg["callbacks"] = existing

    if configurable:
        cfg.setdefault("configurable", {}).update(configurable)
    return cfg


def _maybe_enable_langsmith() -> None:
    """
    LangSmith is enabled purely via environment variables that LangChain reads
    natively (LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY / LANGCHAIN_PROJECT). We
    do not need code to send traces there — we just log whether it is active so
    the operator can confirm the toggle took effect.
    """
    settings = get_observability_settings()
    if settings.langsmith_enabled:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
        log.info("observability.langsmith_enabled", project=settings.langsmith_project)


from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache

# Enable global caching for LLM calls to save tokens and time on duplicate queries
set_llm_cache(InMemoryCache())

def build_llm(
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int = 8000,
    **kwargs,
) -> Any:
    """
    Build a ChatOpenAI client wired to OpenRouter.

    Tracing is NOT attached here; callers attach it per-run via traced_config()
    so callbacks propagate through the whole run tree exactly once.
    """
    # Ensure settings (and thus .env) are loaded before we read the API key,
    # regardless of whether the caller configured logging first.
    get_observability_settings()
    llm = ChatOpenAI(
        model=model_name,
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        temperature=temperature,
        max_retries=3,
        max_tokens=max_tokens,
        **kwargs,
    )
    
    return llm

