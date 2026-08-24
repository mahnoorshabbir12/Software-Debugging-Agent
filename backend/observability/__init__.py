"""
Observability layer for the autonomous debugging agent (Module 21).

Public API:
    - configure_logging():        set up structured logging (idempotent)
    - get_logger(name):           obtain a structlog bound logger
    - bind_log_context(**kw):     attach context (session_id, trace_id, node) to all logs
    - clear_log_context():        remove bound context
    - log_context(**kw):          scoped context binding (context manager)
    - get_observability_settings(): typed, cached settings from the environment
"""

from backend.observability.config import (
    ObservabilitySettings,
    get_observability_settings,
)
from backend.observability.context import (
    correlation_scope,
    get_correlation,
    new_trace_id,
)
from backend.observability.logging import (
    bind_log_context,
    clear_log_context,
    configure_logging,
    get_logger,
    log_context,
)
from backend.observability.setup import init_observability
from backend.observability.spans import (
    SpanRecord,
    emit_span,
    register_sink,
)

__all__ = [
    "ObservabilitySettings",
    "get_observability_settings",
    "configure_logging",
    "init_observability",
    "get_logger",
    "bind_log_context",
    "clear_log_context",
    "log_context",
    "correlation_scope",
    "get_correlation",
    "new_trace_id",
    "SpanRecord",
    "emit_span",
    "register_sink",
]
