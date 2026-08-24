"""
Database sink + query helpers for the span store.

Concept: a sink that persists
-----------------------------
`database_sink` is a span exporter (see spans.py) that writes each finished span
to the SpanEvent table. It is registered at startup via init_observability().

We persist only terminal spans (status ok/error), computing LLM cost at write
time. Each write uses its own short-lived Session, which is safe from the
background investigation thread.

The fetch_* helpers are the read side used by the API in Stage 4.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, select

from backend.database.core import engine
from backend.database.models import DebugSession, SpanEvent
from backend.observability.config import get_observability_settings
from backend.observability.logging import get_logger
from backend.observability.metrics import estimate_cost, summarize_spans
from backend.observability.spans import SpanRecord

log = get_logger("observability.store")


def database_sink(span: SpanRecord) -> None:
    """Persist a finished span to the SpanEvent table."""
    settings = get_observability_settings()
    if not settings.enabled:
        return
    if span.status == "running":
        return  # only persist terminal spans

    cost = span.cost_usd
    if span.kind == "llm" and cost is None:
        cost = estimate_cost(span.model, span.prompt_tokens, span.completion_tokens)

    row = SpanEvent(
        debug_session_id=span.session_id,
        trace_id=span.trace_id,
        span_id=span.span_id,
        parent_span_id=span.parent_span_id,
        kind=span.kind,
        name=span.name,
        node=span.node,
        status=span.status,
        start_ts=span.start_ts,
        end_ts=span.end_ts,
        duration_ms=span.duration_ms,
        model=span.model,
        prompt_tokens=span.prompt_tokens,
        completion_tokens=span.completion_tokens,
        total_tokens=span.total_tokens,
        cost_usd=cost,
        tool_name=span.tool_name,
        input=span.input,
        output=span.output,
        error=span.error,
    )
    try:
        with Session(engine) as db:
            db.add(row)
            db.commit()
    except Exception:  # pragma: no cover - never let persistence break a run
        log.warning("observability.persist_failed", span_id=span.span_id, exc_info=True)


# --- Read side (used by the API in Stage 4) ---------------------------------


def fetch_trace(session_id: int) -> list[SpanEvent]:
    """Return all spans for a debug session, oldest first (the full timeline)."""
    with Session(engine) as db:
        stmt = (
            select(SpanEvent)
            .where(SpanEvent.debug_session_id == session_id)
            .order_by(SpanEvent.created_at)
        )
        return list(db.exec(stmt).all())


def fetch_session_metrics(session_id: int) -> dict:
    """Aggregate the metrics for one debug session."""
    spans = fetch_trace(session_id)
    summary = summarize_spans(spans)
    summary["session_id"] = session_id
    summary["span_count"] = len(spans)
    return summary


def fetch_overview() -> dict:
    """
    System-wide observability rollup for the dashboard (all sessions).

    Uses SQL aggregation so it stays cheap even as the span table grows.
    """
    with Session(engine) as db:
        total_spans = db.exec(select(func.count()).select_from(SpanEvent)).one()
        total_tokens = db.exec(
            select(func.coalesce(func.sum(SpanEvent.total_tokens), 0))
        ).one()
        total_cost = db.exec(
            select(func.coalesce(func.sum(SpanEvent.cost_usd), 0.0))
        ).one()
        llm_calls = db.exec(
            select(func.count()).select_from(SpanEvent).where(SpanEvent.kind == "llm")
        ).one()
        tool_calls = db.exec(
            select(func.count()).select_from(SpanEvent).where(SpanEvent.kind == "tool")
        ).one()
        errors = db.exec(
            select(func.count()).select_from(SpanEvent).where(SpanEvent.status == "error")
        ).one()
        traced_sessions = db.exec(
            select(func.count(func.distinct(SpanEvent.debug_session_id)))
        ).one()

    return {
        "total_spans": int(total_spans or 0),
        "traced_sessions": int(traced_sessions or 0),
        "llm_calls": int(llm_calls or 0),
        "tool_calls": int(tool_calls or 0),
        "errors": int(errors or 0),
        "total_tokens": int(total_tokens or 0),
        "total_cost_usd": round(float(total_cost or 0.0), 6),
    }
