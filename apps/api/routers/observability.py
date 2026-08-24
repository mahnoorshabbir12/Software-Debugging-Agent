"""
Observability API endpoints (Module 21).

Exposes the span store and metrics so the React dashboard can render the trace
timeline, per-session metrics, and a system-wide health overview.

All Module 21 HTTP surface lives here (full paths, no prefix) so it is easy to
find and reason about as one unit.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.database.core import get_session
from backend.database.models import DebugSession
from backend.observability.store import (
    fetch_overview,
    fetch_session_metrics,
    fetch_trace,
)
from apps.api.schemas import (
    ObservabilityOverviewResponse,
    SessionMetricsResponse,
    SpanResponse,
)

router = APIRouter(tags=["Observability"])


def _require_session(id: int, session: Session) -> DebugSession:
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation


@router.get("/investigations/{id}/traces", response_model=List[SpanResponse])
def get_investigation_traces(id: int, session: Session = Depends(get_session)):
    """Return the full span timeline (LLM/tool/node) for an investigation."""
    _require_session(id, session)
    return fetch_trace(id)


@router.get("/investigations/{id}/metrics", response_model=SessionMetricsResponse)
def get_investigation_metrics(id: int, session: Session = Depends(get_session)):
    """Return aggregated metrics (tokens, cost, latency, errors) for a session."""
    _require_session(id, session)
    return fetch_session_metrics(id)


@router.get("/observability/overview", response_model=ObservabilityOverviewResponse)
def get_observability_overview():
    """System-wide observability rollup for the dashboard health card."""
    return fetch_overview()
