# Module 27: Production Hardening

This module applies standard production-ready safeguards to the autonomous debugger to ensure it is resilient, cost-effective, and safe from infinite loops.

## 1. Concept

Production hardening involves protecting an application against the realities of the real world: network latency, API rate limits, duplicate executions, and infinite loops. In agentic systems, this primarily revolves around LLM reliability and Graph execution limits.

## 2. Problem

Before this module:
- If OpenRouter returned a `503 Service Unavailable`, the entire debugging session crashed immediately.
- If an agent got stuck and requested the exact same code chunk 5 times, it cost 5x the API tokens and took 5x the time.
- If the agent entered a stubborn state where it endlessly bounced between `HypothesisAgent` and `InvestigateAgent`, it could spin forever, burning through massive token budgets.

## 3. Why this project needs it

Autonomous agents are inherently non-deterministic. Because they control their own control flow, they can easily trap themselves in loops. Furthermore, since they operate unattended (e.g. in a CI pipeline overnight), they must gracefully handle API flakiness without a human needing to click "Retry".

## 4. Alternatives & Decisions

### LLM Retries
- **Custom `while/try/except` loop:** Manual implementation of exponential backoff. Error prone.
- **`Tenacity` library:** Powerful, but requires wrapping every function.
- **LangChain `.with_retry()` or `max_retries` (chosen):** Natively supported by the `ChatOpenAI` client. It automatically respects `Retry-After` headers and applies exponential backoff for 429/503 errors.

### Caching
- **RedisCache:** Distributed, persistent cache. Overkill for a local single-node agent.
- **InMemoryCache (chosen):** Keeps identical LLM calls cached in memory for the duration of the process. Instant lookups, zero infrastructure overhead.

## 5. Architecture & data flow

```
[Agent Node]
     │
     ▼
[InMemory Cache Check] ──▶ (Hit) ──▶ [Return Cached Response instantly]
     │
     ▼ (Miss)
[ChatOpenAI (max_retries=3)]
     │
     ├─▶ (Network Error) ──▶ [Exponential Backoff & Retry]
     │
     └─▶ (Success) ───────▶ [Save to Cache & Return]
```

## 6. Implementation

- `backend/llm.py` — Configured `max_retries=3` on the `ChatOpenAI` client.
- `backend/llm.py` — Enabled `langchain_core.globals.set_llm_cache(InMemoryCache())`.
- `backend/agents/supervisor.py` — Added a `recursion_limit` parameter to `SupervisorGraph.run()` which is passed down to LangGraph to cap execution edges.

## 7. Verification

- `scratch/test_caching.py` verified that an identical LLM prompt evaluated in ~3.0s the first time and 0.00s the second time.
- `scratch/test_recursion.py` verified that setting an artificially low `recursion_limit` forced the graph to abort safely with a `GraphRecursionError`.

## Transferable Rules

> **Use LLM Caching when:** your agentic system runs loops and may re-evaluate the same state multiple times, wasting tokens.
>
> **Use Recursion Limits when:** running any non-deterministic graph or loop in production. Never deploy an LLM-driven loop without a hard stop.
