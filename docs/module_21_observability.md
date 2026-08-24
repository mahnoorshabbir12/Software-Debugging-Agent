# Module 21: Agent Observability

This module gives the debugging agent an observability layer so we can answer not
just *"did the agent fail?"* but *"where and why did it fail, how long did it
take, and how much did it cost?"* — by capturing LLM calls, tokens, latency,
tool calls, graph-node transitions, retries, and failures as structured logs, a
queryable trace store, live events, and dashboard metrics.

## 1. Concept

Observability rests on three pillars:

- **Logs** — discrete, timestamped events. We make them *structured* (JSON
  key/value) instead of free text so they can be filtered and correlated.
- **Traces / spans** — a *span* is one timed operation (an LLM call, a tool call,
  a graph node). Spans that share a `trace_id` form the *trace* of one
  investigation.
- **Metrics** — aggregates over spans: total tokens, cost, latency, error counts.

## 2. Problem

Before this module the agent was a black box. Four separate agents each built
their own `ChatOpenAI`, there was no logging setup, the `ToolCall` table was
unused, and a failed run left no record of which LLM call or tool caused it. You
could not measure token cost or latency, or see what the agent did.

## 3. Why this project needs it

An autonomous, multi-step LangGraph agent makes many LLM and tool calls per run
and loops on self-correction. When it produces a wrong patch or stalls, we must
locate the exact step that failed and see its inputs, latency, and token cost.
Observability is what makes an agentic system debuggable and affordable.

## 4. Alternatives & Decisions

### Tracing backend
- **LangSmith (managed SaaS):** zero-code via env vars, rich hosted trace UI, but
  external and does not populate our own DB/dashboard.
- **OpenTelemetry + collector:** vendor-neutral and portable, but heavy infra for
  a single-node app.
- **Self-hosted callback + DB + dashboard (chosen):** a custom LangChain
  callback handler feeds spans into our own Postgres/SQLite and dashboard.

**Decision:** self-hosted as the core (highest learning value; reuses our DB +
SSE + React), with **LangSmith as an optional env-var toggle** for deep hosted
traces. OpenTelemetry deferred until there is a multi-service topology.

### Instrumentation mechanism
- **LangChain `BaseCallbackHandler` (chosen):** one handler observes LLMs, tools,
  and graph nodes uniformly, and picks up nested calls via run-tree propagation.
- Manual wrapping of every `.invoke()` — rejected (repetitive, misses nested
  LangGraph internals).

### Where the tracer attaches
- Via the **run config** at each `.invoke()` (through `traced_config()`), **not**
  bound to the model object. Attaching in both places would double-count spans;
  config-only gives exactly one attach point per run while still propagating to
  nested tool/LLM/node calls.

### Structured logging
- **`structlog` (chosen)** for first-class structured + contextual logging bound
  to `session_id`/`trace_id`/`node`. Stdlib logging was the fallback.

## 5. Architecture & data flow

```
Agents (triage/hypothesis/evidence/patch)
    │  build_llm()  +  .invoke(config=traced_config())
    ▼
TracingCallbackHandler  ── on_llm/tool/chain start&end ──▶  SpanRecord
    │
    ▼   emit_span() fans out to registered sinks
    ├──▶ logging_sink   → structured JSON logs
    ├──▶ database_sink  → SpanEvent table (persist + cost)
    └──▶ sse_sink       → EventDispatcher → browser (live)
                                   │
        API: /investigations/{id}/traces · /metrics · /observability/overview
                                   ▼
                React: Investigation "Observability" tab + Dashboard card
```

Correlation (`session_id`/`trace_id`/`node`) is stored in `contextvars`
(`backend/observability/context.py`) so it is isolated per task/thread and read
by both the logger and the tracer at event time.

## 6. Implementation

- `backend/observability/config.py` — env-driven `ObservabilitySettings`
  (enable, log level/JSON, sampling, prompt redaction, LangSmith).
- `backend/observability/logging.py` — `structlog` + stdlib bridge; `log_context`.
- `backend/observability/context.py` — correlation contextvars + `correlation_scope`.
- `backend/observability/spans.py` — `SpanRecord`, sink registry, truncation/redaction.
- `backend/observability/callbacks.py` — `TracingCallbackHandler` (the seam).
- `backend/observability/metrics.py` — token→cost price map + aggregation.
- `backend/observability/store.py` — `database_sink` + `fetch_trace/metrics/overview`.
- `backend/observability/streaming.py` — `sse_sink` (reuses Module 19 dispatcher).
- `backend/observability/setup.py` — `init_observability()` bootstrap.
- `backend/llm.py` — shared `build_llm()` + `traced_config()` (removes 4x duplication).
- `backend/database/models.py` — new `SpanEvent` table (+ Alembic migration).
- `apps/api/routers/observability.py` — traces / metrics / overview endpoints.
- `frontend` — Investigation "Observability" tab + Dashboard "Agent Observability" card.

## 7. What we observe → where it's captured

| Target | Seam |
|---|---|
| LLM calls, tokens, latency | `on_llm_start/end` (model, `usage_metadata`) |
| Tool calls | `on_tool_start/end` |
| Graph node transitions | `on_chain_start/end`, filtered by `langgraph_node` |
| Failures | `on_*_error` → `status="error"` spans |
| Cost | `metrics.estimate_cost()` at persist time |

## 8. Verification

- A real `triage` call recorded one LLM span with tokens/latency/model (no
  duplication despite `with_structured_output`).
- A real tool (`read_file`) and a compiled LangGraph node recorded tool and
  chain spans; a nested LLM call inside the node was captured via run-tree
  propagation (single span, shared `trace_id`).
- Persistence: spans written to `SpanEvent`; cost computed
  (142 in / 79 out on llama-3.1-8b ⇒ `$5.21e-06`); `fetch_*` aggregates correct.
- API: `/traces`, `/metrics`, `/observability/overview` return correct data and
  deliberately omit raw prompt/output payloads.
- End-to-end: `triage`→`hypothesis` in one trace, plus a forced 401 that produced
  an `error` span (`OpenAIAuthenticationError`) with node attribution.

## 9. Privacy note

Per the design system, the UI never shows raw chain-of-thought. Prompts/outputs
are truncated and kept in the backend span store only (with an
`OBSERVABILITY_REDACT_PROMPTS` switch); API/UI expose action summaries + metrics.

## Transferable Rules

> **Instrument at the framework's seam, once.** Use a single callback handler
> attached via run config so LLM, tool, and node events are captured uniformly
> and nested calls propagate — instead of wrapping every call site.

> **Separate producers from exporters.** A tracer should emit normalized span
> records; pluggable sinks decide whether to log, persist, or stream them. Adding
> a new destination never touches the tracer.

> **Correlate with contextvars.** Bind `trace_id`/`session_id` once at the top of
> a run; contextvars carry them through the whole call tree without threading
> arguments, and stay isolated per task/thread.

> **Keep raw model I/O out of the UI.** Store it (optionally redacted) for backend
> debugging; surface only summaries and metrics.

## Known follow-up (integration debt, out of scope here)

The API still runs the *simulated* `runner.py`, and `supervisor.py` imports a
renamed model (`Investigation` vs `DebugSession`). Once the real `SupervisorGraph`
is wired into the runner, the observability layer lights up automatically because
it is attached at the LLM/tool/graph seams — no further tracing work required.
