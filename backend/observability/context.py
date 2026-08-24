"""
Correlation context for observability.

Concept: correlation IDs
------------------------
A single investigation produces many spans (LLM calls, tool calls, graph node
transitions) across many functions. To stitch them into one coherent trace we
attach the same identifiers to every span:

    session_id : the DebugSession this run belongs to (links spans to the DB row)
    trace_id   : one investigation run (a fresh uuid per run)
    node       : which agent/graph node is currently executing (triage, patch...)

We store these in `contextvars`, which are isolated per-thread and per-async-task.
That means the background investigation thread for session 5 and session 6 keep
separate context automatically — no manual passing of IDs through every call.

Both the tracer (callbacks.py) and structured logging read from here, so a log
line and the span it describes always carry the same correlation fields.
"""

from __future__ import annotations

import contextlib
import contextvars
import uuid
from typing import Any, Iterator, Optional

import structlog

# The three correlation dimensions, each isolated per task/thread.
_session_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "obs_session_id", default=None
)
_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "obs_trace_id", default=None
)
_node: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "obs_node", default=None
)


def new_trace_id() -> str:
    """Generate a fresh trace id for one investigation run."""
    return uuid.uuid4().hex


def get_session_id() -> Optional[int]:
    return _session_id.get()


def get_trace_id() -> Optional[str]:
    return _trace_id.get()


def get_node() -> Optional[str]:
    return _node.get()


def get_correlation() -> dict[str, Any]:
    """Return the current correlation fields (for attaching to spans/logs)."""
    return {
        "session_id": _session_id.get(),
        "trace_id": _trace_id.get(),
        "node": _node.get(),
    }


@contextlib.contextmanager
def correlation_scope(
    session_id: Optional[int] = None,
    trace_id: Optional[str] = None,
    node: Optional[str] = None,
) -> Iterator[None]:
    """
    Bind correlation fields for the duration of a `with` block.

    Only the arguments you pass are overridden; the others inherit from the
    surrounding scope. This lets an agent do `with correlation_scope(node="triage")`
    while still inheriting the session_id/trace_id set by the runner higher up.

    The same values are mirrored into structlog's contextvars so every log line
    inside the block carries them too.
    """
    tokens: list = []
    struct_keys: dict[str, Any] = {}

    if session_id is not None:
        tokens.append((_session_id, _session_id.set(session_id)))
        struct_keys["session_id"] = session_id
    if trace_id is not None:
        tokens.append((_trace_id, _trace_id.set(trace_id)))
        struct_keys["trace_id"] = trace_id
    if node is not None:
        tokens.append((_node, _node.set(node)))
        struct_keys["node"] = node

    struct_tokens = structlog.contextvars.bind_contextvars(**struct_keys) if struct_keys else {}
    try:
        yield
    finally:
        # Reset in reverse order so nested scopes restore correctly.
        for var, token in reversed(tokens):
            var.reset(token)
        if struct_tokens:
            structlog.contextvars.reset_contextvars(**struct_tokens)
