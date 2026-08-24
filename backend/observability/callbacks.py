"""
TracingCallbackHandler: the instrumentation seam.

Concept: LangChain callbacks
----------------------------
LangChain and LangGraph invoke a callback handler at well-defined lifecycle
points: when an LLM/chat model starts and ends, when a tool starts and ends, and
when a chain/graph node starts and ends. By implementing one handler we observe
*every* LLM call, tool call, and graph transition across all four agents without
editing their internal logic — we just attach the handler to the run config.

Why one handler (vs. wrapping each .invoke())
---------------------------------------------
The agents call `.invoke()` in ~6 places, and LangGraph runs tools/nodes we do
not call directly. A single callback handler captures all of them uniformly and
picks up nested calls via LangChain's run-tree propagation.

What we capture per span
------------------------
- LLM: model, prompt/completion/total tokens, latency, errors.
- Tool: tool name, input, output, latency, errors.
- Graph node: node name + latency (filtered to real LangGraph nodes).

Correlation (session_id / trace_id / node) is read from contextvars at event
time, so spans automatically link to the right investigation.

Resilience: `raise_error = False` and defensive try/except mean a bug in
tracing can never crash an investigation.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from backend.observability.context import get_node, get_session_id, get_trace_id
from backend.observability.logging import get_logger
from backend.observability.spans import SpanRecord, emit_span, redact, truncate

log = get_logger("observability.tracer")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_model(serialized: Optional[dict], kwargs: dict) -> Optional[str]:
    """Best-effort model-name extraction across langchain versions/providers."""
    inv = kwargs.get("invocation_params") or {}
    model = inv.get("model") or inv.get("model_name")
    if not model and serialized:
        skwargs = serialized.get("kwargs") or {}
        model = skwargs.get("model") or skwargs.get("model_name")
    if not model:
        md = kwargs.get("metadata") or {}
        model = md.get("ls_model_name")
    return model


def _extract_token_usage(response: LLMResult) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Pull token counts from wherever the provider put them.

    OpenAI-style responses expose `llm_output['token_usage']`; newer langchain
    also attaches `usage_metadata` to the generated message. We check both.
    """
    prompt = completion = total = None

    llm_output = response.llm_output or {}
    usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
    if usage:
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")

    if total is None:
        try:
            gen = response.generations[0][0]
            message = getattr(gen, "message", None)
            meta = getattr(message, "usage_metadata", None) or {}
            prompt = prompt if prompt is not None else meta.get("input_tokens")
            completion = completion if completion is not None else meta.get("output_tokens")
            total = total if total is not None else meta.get("total_tokens")
        except (AttributeError, IndexError, TypeError):
            pass

    if total is None and (prompt is not None or completion is not None):
        total = (prompt or 0) + (completion or 0)

    return prompt, completion, total


class TracingCallbackHandler(BaseCallbackHandler):
    """A single handler that turns LangChain lifecycle events into SpanRecords."""

    # If a callback raises, log it but never propagate into the agent run.
    raise_error = False

    def __init__(self) -> None:
        # run_id (str) -> in-flight span metadata
        self._runs: dict[str, dict[str, Any]] = {}

    # -- internal helpers -----------------------------------------------------

    def _open(self, run_id: UUID, name: str, kind: str, **extra: Any) -> None:
        self._runs[str(run_id)] = {
            "name": name,
            "kind": kind,
            "start_perf": time.perf_counter(),
            "start_iso": _now_iso(),
            **extra,
        }

    def _close(
        self,
        run_id: UUID,
        parent_run_id: Optional[UUID],
        status: str,
        *,
        output: Optional[str] = None,
        error: Optional[str] = None,
        **fields: Any,
    ) -> None:
        started = self._runs.pop(str(run_id), None)
        if started is None:
            return
        duration_ms = round((time.perf_counter() - started["start_perf"]) * 1000, 2)
        span = SpanRecord(
            span_id=str(run_id),
            parent_span_id=str(parent_run_id) if parent_run_id else None,
            name=started["name"],
            kind=started["kind"],
            status=status,
            trace_id=get_trace_id(),
            session_id=get_session_id(),
            node=get_node(),
            start_ts=started["start_iso"],
            end_ts=_now_iso(),
            duration_ms=duration_ms,
            input=started.get("input"),
            output=output,
            error=error,
            model=started.get("model"),
            tool_name=started.get("tool_name"),
            **fields,
        )
        emit_span(span)

    # -- LLM / chat model -----------------------------------------------------

    def on_chat_model_start(
        self, serialized, messages, *, run_id: UUID, parent_run_id=None, **kwargs
    ) -> None:
        self._open(
            run_id,
            name="chat_model",
            kind="llm",
            model=_extract_model(serialized, kwargs),
            input=redact(messages),
        )

    def on_llm_start(
        self, serialized, prompts, *, run_id: UUID, parent_run_id=None, **kwargs
    ) -> None:
        self._open(
            run_id,
            name="llm",
            kind="llm",
            model=_extract_model(serialized, kwargs),
            input=redact(prompts),
        )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        prompt_tokens, completion_tokens, total_tokens = _extract_token_usage(response)
        try:
            text = response.generations[0][0].text
        except (AttributeError, IndexError, TypeError):
            text = None
        self._close(
            run_id,
            parent_run_id,
            "ok",
            output=redact(text),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        self._close(run_id, parent_run_id, "error", error=truncate(repr(error)))

    # -- tools ----------------------------------------------------------------

    def on_tool_start(
        self, serialized, input_str, *, run_id: UUID, parent_run_id=None, **kwargs
    ) -> None:
        tool_name = (serialized or {}).get("name") or kwargs.get("name") or "tool"
        self._open(
            run_id,
            name=tool_name,
            kind="tool",
            tool_name=tool_name,
            input=truncate(input_str),
        )

    def on_tool_end(self, output, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        self._close(run_id, parent_run_id, "ok", output=truncate(output))

    def on_tool_error(self, error: BaseException, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        self._close(run_id, parent_run_id, "error", error=truncate(repr(error)))

    # -- chains / graph nodes -------------------------------------------------

    def on_chain_start(
        self, serialized, inputs, *, run_id: UUID, parent_run_id=None, **kwargs
    ) -> None:
        # LangGraph tags true node executions with `langgraph_node` in metadata.
        # We record only those to avoid the noise of every internal Runnable.
        metadata = kwargs.get("metadata") or {}
        node = metadata.get("langgraph_node")
        if not node:
            return
        self._open(run_id, name=node, kind="chain", input=None)

    def on_chain_end(self, outputs, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        if str(run_id) in self._runs:
            self._close(run_id, parent_run_id, "ok")

    def on_chain_error(self, error: BaseException, *, run_id: UUID, parent_run_id=None, **kwargs) -> None:
        if str(run_id) in self._runs:
            self._close(run_id, parent_run_id, "error", error=truncate(repr(error)))
