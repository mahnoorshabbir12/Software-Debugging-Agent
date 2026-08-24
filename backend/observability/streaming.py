"""
SSE streaming sink.

Concept: live observability
---------------------------
Persisting spans (store.py) lets us query a trace *after* the fact. But the
design system wants the Agent Activity panel to update *while* the agent works.
This sink pushes each finished span onto the existing Server-Sent Events stream
(EventDispatcher) so the browser sees LLM calls, tool calls, and node
transitions in real time.

It reuses the EventDispatcher built in Module 19, which already bridges the sync
background thread to the asyncio event loop, so we do not invent a second
streaming mechanism. If no browser is listening to a session, emit() is a no-op.

Privacy: only lightweight metadata is streamed (never raw prompts / outputs).
"""

from __future__ import annotations

from backend.agents.events import EventDispatcher
from backend.observability.config import get_observability_settings
from backend.observability.spans import SpanRecord


def sse_sink(span: SpanRecord) -> None:
    if not get_observability_settings().enabled:
        return
    if span.status == "running":
        return
    if span.session_id is None:
        return  # ad-hoc spans (tests / CLI without a session) are not streamed

    payload = {
        "span_id": span.span_id,
        "trace_id": span.trace_id,
        "kind": span.kind,
        "name": span.name,
        "node": span.node,
        "status": span.status,
        "duration_ms": span.duration_ms,
        "model": span.model,
        "total_tokens": span.total_tokens,
        "cost_usd": span.cost_usd,
        "tool_name": span.tool_name,
        "error": span.error,
        "timestamp": span.end_ts,
    }
    EventDispatcher.emit(span.session_id, "observability.span", payload)
