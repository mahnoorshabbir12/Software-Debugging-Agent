from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Repository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    url: str
    default_branch: str = "main"

class DebugSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: Optional[int] = Field(default=None, foreign_key="repository.id")
    branch: str = Field(default="main")
    bug_report: str = Field(default="")
    status: str = Field(default="idle") # idle, starting, running, paused, stopping, stopped, completed, failed
    current_step: Optional[str] = None
    current_action: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    final_patch_id: Optional[int] = None
    
    hypotheses: List["Hypothesis"] = Relationship(back_populates="debug_session")

class Hypothesis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    debug_session_id: int = Field(foreign_key="debugsession.id")
    title: str
    description: str
    status: str = Field(default="untested") # untested, supported, refuted
    
    debug_session: DebugSession = Relationship(back_populates="hypotheses")
    evidence: List["Evidence"] = Relationship(back_populates="hypothesis")
    patches: List["Patch"] = Relationship(back_populates="hypothesis")

class Evidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hypothesis_id: int = Field(foreign_key="hypothesis.id")
    type: str # string, file, test_output
    content: str
    is_supporting: bool = True
    
    hypothesis: Hypothesis = Relationship(back_populates="evidence")

class Patch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hypothesis_id: int = Field(foreign_key="hypothesis.id")
    file_path: str
    original_snippet: str
    new_snippet: str
    status: str = Field(default="generated") # generated, valid, invalid
    
    hypothesis: Hypothesis = Relationship(back_populates="patches")
    test_runs: List["TestRun"] = Relationship(back_populates="patch")

class TestRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patch_id: int = Field(foreign_key="patch.id")
    passed: bool
    test_output: Optional[str] = None
    lint_output: Optional[str] = None
    type_output: Optional[str] = None
    
    patch: Patch = Relationship(back_populates="test_runs")

class ToolCall(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    debug_session_id: int = Field(foreign_key="debugsession.id")
    node: str # e.g. 'investigate', 'patch'
    tool_name: str
    args_json: str
    result_json: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SpanEvent(SQLModel, table=True):
    """
    The canonical observability trace store (Module 21).

    One row = one finished span (an LLM call, a tool call, or a graph node
    execution). Spans that share a `trace_id` form one investigation trace;
    `debug_session_id` links the trace back to the DebugSession it belongs to.

    Type-specific columns are nullable: `model`/token/`cost_usd` are populated
    for LLM spans, `tool_name` for tool spans. This single-table design keeps the
    "give me the whole trace for session N" query trivial.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    debug_session_id: Optional[int] = Field(
        default=None, foreign_key="debugsession.id", index=True
    )
    trace_id: Optional[str] = Field(default=None, index=True)
    span_id: str = Field(index=True)
    parent_span_id: Optional[str] = None

    kind: str  # 'llm' | 'tool' | 'chain'
    name: str
    node: Optional[str] = None
    status: str = Field(default="ok")  # 'ok' | 'error'

    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    duration_ms: Optional[float] = None

    # LLM-specific
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None

    # Tool-specific
    tool_name: Optional[str] = None

    # Truncated payloads (kept for backend drill-down; not exposed raw in the UI)
    input: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
