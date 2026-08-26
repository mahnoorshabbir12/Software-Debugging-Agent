"""
Shared LLM factory + traced run config.

Concept: LLM Gateway via LiteLLM Proxy (Module 28)
---------------------------------------------------
Before Module 28, build_llm() pointed every agent directly at OpenRouter.
If OpenRouter went down, every agent crashed. Switching providers meant
editing Python code.

Now, build_llm() points at the **LiteLLM Proxy** (a lightweight reverse-
proxy for LLM APIs running as a Docker sidecar). The proxy handles:
  - Model aliasing: agents request "debugger/main-model", the proxy
    resolves it to the real provider model.
  - Provider failover: if OpenRouter returns 503, the proxy automatically
    retries against the fallback provider (e.g., local Ollama).
  - Gateway-level caching (L2): shared across all workers.

Architecture:
  Agent → build_llm() → LiteLLM Proxy (localhost:4000) → Provider API
                ↓
          ChatOpenAI(base_url=LITELLM_BASE_URL)

The factory still centralizes construction so all cross-cutting concerns
(tracing, caching, parameter defaults) live in ONE place.

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

# ── Gateway configuration ────────────────────────────────────────────────────
# These read from environment variables so that switching providers or models
# is a config change, not a code change. Defaults point at a local LiteLLM
# Proxy instance (started via `docker compose up litellm`).
DEFAULT_MODEL = os.environ.get("LLM_MODEL_NAME", "debugger/main-model")
LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000/v1")

MAX_PROMPT_TOKENS = 2600

def get_prompt_budget() -> int:
    """Expose the safe prompt token budget for the entire backend."""
    return MAX_PROMPT_TOKENS
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

# L1 cache: fast in-process cache for identical prompts within a single worker.
# The LiteLLM Proxy provides an L2 gateway-level cache shared across workers.
set_llm_cache(InMemoryCache())

class SingleToolChatOpenAI(ChatOpenAI):
    def bind_tools(self, tools, **kwargs):
        # Some providers (e.g., OpenRouter's LLaMA 3.1 8B) throw a 400 error
        # if parallel_tool_calls is enabled. We override bind_tools to force it
        # off. The LiteLLM Proxy's `drop_params: true` setting also helps, but
        # this is a defence-in-depth measure at the client level.
        kwargs["parallel_tool_calls"] = False
        return super().bind_tools(tools, **kwargs)

def build_llm(
    model_name: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1500,
    **kwargs,
) -> Any:
    """
    Build a ChatOpenAI client wired to the LiteLLM Proxy gateway.

    The gateway resolves the virtual model name (e.g., "debugger/main-model")
    to a real provider deployment and handles failover automatically.

    Tracing is NOT attached here; callers attach it per-run via traced_config()
    so callbacks propagate through the whole run tree exactly once.
    """
    # Ensure settings (and thus .env) are loaded before we read env vars,
    # regardless of whether the caller configured logging first.
    get_observability_settings()

    resolved_model = model_name or DEFAULT_MODEL

    llm = SingleToolChatOpenAI(
        model=resolved_model,
        base_url=LITELLM_BASE_URL,
        api_key=os.environ.get("LITELLM_API_KEY", "sk-debugger-dev"),
        temperature=temperature,
        max_retries=3,
        max_tokens=max_tokens,
        **kwargs,
    )
    
    return llm

