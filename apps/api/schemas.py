from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RepositoryCreate(BaseModel):
    name: str
    url: str

class RepositoryResponse(BaseModel):
    id: int
    name: str
    url: str
    default_branch: str

class DebugSessionCreate(BaseModel):
    repository_id: int
    branch: Optional[str] = "main"
    bug_report: Optional[str] = ""

class DebugSessionResponse(BaseModel):
    id: int
    repository_id: Optional[int] = None
    repository_name: Optional[str] = None
    branch: str
    bug_report: str
    status: str
    current_step: Optional[str] = None
    current_action: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    final_patch_id: Optional[int] = None
class EvidenceResponse(BaseModel):
    id: int
    hypothesis_id: int
    type: str
    content: str
    is_supporting: bool

class PatchResponse(BaseModel):
    id: int
    hypothesis_id: int
    file_path: str
    original_snippet: str
    new_snippet: str
    status: str

class EventResponse(BaseModel):
    message: str
    timestamp: datetime


class SpanResponse(BaseModel):
    """
    One observability span for the trace timeline.

    Note: raw prompt/tool input & output are deliberately omitted — per the
    design system, the UI shows action summaries and metrics, not raw reasoning.
    """
    id: int
    span_id: str
    parent_span_id: Optional[str] = None
    trace_id: Optional[str] = None
    kind: str
    name: str
    node: Optional[str] = None
    status: str
    duration_ms: Optional[float] = None
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    tool_name: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class SessionMetricsResponse(BaseModel):
    session_id: int
    span_count: int
    llm_calls: int
    tool_calls: int
    node_transitions: int
    errors: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    total_duration_ms: float
    llm_duration_ms: float


class ObservabilityOverviewResponse(BaseModel):
    total_spans: int
    traced_sessions: int
    llm_calls: int
    tool_calls: int
    errors: int
    total_tokens: int
    total_cost_usd: float
