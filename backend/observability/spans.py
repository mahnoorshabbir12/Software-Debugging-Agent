"""
Span model and sink registry.

Concept: spans and traces
-------------------------
A *span* is one timed operation with a start, an end, a status, and metadata
(e.g. "the triage LLM call took 812ms and used 430 tokens"). A *trace* is the
set of spans that share a trace_id — the whole investigation.

Concept: exporters / sinks
--------------------------
The tracer (callbacks.py) produces SpanRecords but should not care where they
go. A *sink* is a function that receives a finished span and does something with
it: log it, write it to the database, or stream it to the browser. This is the
same pattern OpenTelemetry calls "exporters".

Stage 2 registers only the logging sink. Stage 3 adds a database sink and
Stage 4 adds an SSE sink — without touching the tracer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional

from backend.observability.config import get_observability_settings
from backend.observability.logging import get_logger

log = get_logger("observability.span")

# A sink is any callable that consumes a finished span.
Sink = Callable[["SpanRecord"], None]


@dataclass
class SpanRecord:
    """One timed operation in a trace."""

    span_id: str
    name: str
    kind: str  # "llm" | "tool" | "chain"
    status: str = "running"  # "running" | "ok" | "error"

    parent_span_id: Optional[str] = None
    trace_id: Optional[str] = None
    session_id: Optional[int] = None
    node: Optional[str] = None

    start_ts: Optional[str] = None  # ISO wall-clock start
    end_ts: Optional[str] = None
    duration_ms: Optional[float] = None

    input: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

    # LLM-specific
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None

    # Tool-specific
    tool_name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- Sink registry -----------------------------------------------------------

_SINKS: list[Sink] = []


def register_sink(sink: Sink) -> None:
    """Register a sink to receive finished spans (idempotent)."""
    if sink not in _SINKS:
        _SINKS.append(sink)


def clear_sinks() -> None:
    _SINKS.clear()


def emit_span(span: SpanRecord) -> None:
    """
    Fan a finished span out to all registered sinks.

    A failing sink must never break the agent: every sink call is isolated in a
    try/except so one broken exporter cannot crash an investigation.
    """
    for sink in list(_SINKS):
        try:
            sink(span)
        except Exception:  # pragma: no cover - defensive
            log.warning(
                "observability.sink_error",
                sink=getattr(sink, "__name__", repr(sink)),
                exc_info=True,
            )


# --- Payload hygiene ---------------------------------------------------------


def truncate(value: Any, max_len: Optional[int] = None) -> Optional[str]:
    """Stringify and cap a payload so logs/DB don't store megabytes of text."""
    if value is None:
        return None
    settings = get_observability_settings()
    limit = max_len or settings.max_field_len
    text = value if isinstance(value, str) else str(value)
    if len(text) > limit:
        return text[:limit] + f"...[truncated {len(text) - limit} chars]"
    return text


def redact(value: Any) -> Optional[str]:
    """Redact prompt/message text when OBSERVABILITY_REDACT_PROMPTS is enabled."""
    if value is None:
        return None
    if get_observability_settings().redact_prompts:
        return "[REDACTED]"
    return truncate(value)


# --- Default logging sink ----------------------------------------------------


def logging_sink(span: SpanRecord) -> None:
    """Emit each finished span as a structured log line at a level fit for its status."""
    event = f"span.{span.kind}.{span.status}"
    payload = dict(
        span_id=span.span_id,
        name=span.name,
        node=span.node,
        duration_ms=span.duration_ms,
        model=span.model,
        total_tokens=span.total_tokens,
        tool_name=span.tool_name,
        session_id=span.session_id,
        trace_id=span.trace_id,
    )
    if span.status == "error":
        log.error(event, error=span.error, **payload)
    elif span.status == "running":
        log.debug(event, **payload)
    else:
        log.info(event, **payload)


# Register the logging sink as the always-on default exporter.
register_sink(logging_sink)
