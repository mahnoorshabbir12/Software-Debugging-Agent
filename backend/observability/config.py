"""
Observability configuration.

This module centralizes every knob for the observability layer so the rest of
the codebase never reads environment variables directly. Everything is driven by
environment variables (optionally loaded from a local .env file), which keeps
configuration out of code and lets us change behavior per environment without
editing source.

Concept: "Configuration as data"
--------------------------------
Instead of scattering os.getenv() calls across callbacks, logging, and the API,
we read them once here into a single typed object. Callers ask for
`get_observability_settings()` and get a validated, cached settings instance.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field


def _get_bool(name: str, default: bool) -> bool:
    """Parse a truthy/falsy environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class ObservabilitySettings(BaseModel):
    """
    Typed, validated snapshot of all observability configuration.

    We use a Pydantic model (consistent with the rest of the project) so the
    values are validated once and are safe to pass around.
    """

    # Master switch for tracing + persistence (structured logging is always on).
    enabled: bool = Field(default=True)

    # Logging.
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)  # JSON in prod, console renderer in dev

    # Tracing behavior.
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    # Long prompts/tool outputs are truncated before they hit logs/DB so we don't
    # bloat storage or leak huge payloads into the trace store.
    max_field_len: int = Field(default=4000, ge=100)
    # Privacy: design.md forbids exposing raw chain-of-thought in the UI. When
    # true, prompt/message text is redacted before being persisted or streamed.
    redact_prompts: bool = Field(default=False)

    # LangSmith (optional, wired in Stage 6). LangChain reads LANGCHAIN_TRACING_V2
    # and LANGCHAIN_API_KEY natively; we only mirror the toggle here for reporting.
    langsmith_enabled: bool = Field(default=False)
    langsmith_project: str = Field(default="autonomous-debugger")


@lru_cache(maxsize=1)
def get_observability_settings() -> ObservabilitySettings:
    """
    Build (once) and return the observability settings.

    We defensively load a local .env file here because the FastAPI server entry
    point (apps/api/server.py) does not call load_dotenv() the way the CLI does.
    load_dotenv() never overrides variables that are already set in the real
    environment, so this is safe in every environment.

    The result is cached with lru_cache so we parse the environment exactly once
    per process. Tests can call get_observability_settings.cache_clear() to reset.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # python-dotenv is a declared dependency, but never let config loading
        # crash the app just because .env handling failed.
        pass

    return ObservabilitySettings(
        enabled=_get_bool("OBSERVABILITY_ENABLED", True),
        log_level=os.getenv("OBSERVABILITY_LOG_LEVEL", "INFO").upper(),
        log_json=_get_bool("OBSERVABILITY_LOG_JSON", True),
        sample_rate=_get_float("OBSERVABILITY_SAMPLE_RATE", 1.0),
        max_field_len=_get_int("OBSERVABILITY_MAX_FIELD_LEN", 4000),
        redact_prompts=_get_bool("OBSERVABILITY_REDACT_PROMPTS", False),
        langsmith_enabled=_get_bool("LANGCHAIN_TRACING_V2", False),
        langsmith_project=os.getenv("LANGCHAIN_PROJECT", "autonomous-debugger"),
    )
