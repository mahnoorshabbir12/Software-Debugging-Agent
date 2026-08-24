# Autonomous Software Debugging Agent - Memory

This file serves as my internal memory to track what I have accomplished so far, understand the architectural vision, and plan my future steps.

## What has been done

**Phase 1: Foundation & Context Retrieval (Modules 0-5)**
- **Module 0 (Foundation):** Setup `pyproject.toml`, Typer CLI.
- **Module 1 (Repository Understanding):** Built a repository analyzer to traverse, filter, and map file structures.
- **Module 2 (Code Parsing):** Implemented AST-aware chunking to break code down semantically rather than just character-based.
- **Module 3 & 4 (Embeddings & Retrieval):** Set up vector databases (like Qdrant) and hybrid search to retrieve relevant code chunks.
- **Module 5 (Agent Tools):** Packaged the retrieval mechanisms into standardized tools callable by an LLM.

**Phase 2: Agent Architecture & Orchestration (Modules 6-12)**
- **Modules 6-9 (LangGraph Basics):** Built out the foundational state schemas, nodes, and edges required for cyclic graphs.
- **Module 10 (Git Investigation):** Created tools (`backend/agents/evidence.py`) that wrap `git log`, `git blame`, and `git diff` for the agent to use.
- **Module 11 (Web Research):** Integrated DuckDuckGo search so the agent can look up error messages or docs.
- **Module 12 (Supervisor Orchestrator):** Refactored the architecture so a Master Supervisor routes tasks (Investigate, Patch) to specialized Subgraphs.

**Phase 3: Execution, Validation & State (Modules 13-17)**
- **Module 13 (Patch Generation):** Created `backend/patcher.py` to safely apply Search & Replace patches without relying on fragile unified diffs.
- **Module 14 (Docker Sandbox):** Implemented `backend/sandbox.py` using `docker` Python SDK to run untrusted code with zero network access and strict memory/CPU limits.
- **Module 15 (Automated Validation):** Built `backend/validator.py` which copies the project to a temp directory, patches it, spins up the Sandbox, and runs a mini-CI pipeline (`ruff`, `mypy`, `pytest`) to objectively prove if the LLM's fix worked.
- **Module 16 (Self-Correction Loop):** Wired the orchestrator to automatically retry if validation fails. The agent reads test failure logs to update its hypothesis and submit a new patch, bounded by a circuit breaker to avoid infinite loops.
- **Module 17 (Persistent Agent State):** Transitioned the agent's memory to a persistent PostgreSQL database using SQLModel and Alembic, allowing long-running state to survive restarts and be queried.

**Phase 4: Application Layer (Modules 18-20)**
- **Module 18 (FastAPI Backend):** Exposed the agent over REST (`apps/api/`), decoupling API schemas from DB models and using dependency injection for DB sessions.
- **Module 19 (Real-Time Events):** Added SSE streaming (`backend/agents/events.py`, `/investigations/{id}/events`) bridging the sync background runner to the asyncio loop, plus pause/resume/stop/retry controls.
- **Module 20 (React Dashboard):** Built the Vite + React + TS frontend (`frontend/`) with Dashboard, Repositories, and Investigations views over the API.

**Phase 5: Observability (Module 21)**
- **Module 21 (Agent Observability):** Added `backend/observability/` — a self-hosted tracing layer built on a LangChain `TracingCallbackHandler` attached via a new shared LLM factory (`backend/llm.py`, `traced_config()`), so LLM calls, tool calls, and LangGraph node transitions across all four agents are captured as spans. Spans fan out to pluggable sinks: structured `structlog` JSON logs, a persistent `SpanEvent` table (with token→cost estimation), and a live SSE stream reusing the Module 19 dispatcher. Exposed via `/investigations/{id}/traces`, `/investigations/{id}/metrics`, and `/observability/overview`, surfaced in a React "Observability" tab and a Dashboard health card. Optional LangSmith tracing via env toggle.

## Current Module Plan
- **Module 22 - Evaluation Framework:** Build a benchmark of known bugs and measure retrieval (Recall@K, MRR), root-cause accuracy, patch success rate, and efficiency (iterations, tokens, cost) using the Module 21 metrics.

## Known integration debt
- The API still executes the *simulated* `backend/agents/runner.py` (hardcoded steps), and `backend/agents/supervisor.py` imports a renamed model (`Investigation` vs the current `DebugSession`), so `test_supervisor*.py` fail to import. Wiring the real `SupervisorGraph` into the runner (and reconciling the models/migration drift) is the prerequisite for observing the full pipeline end-to-end through the API. The observability layer already attaches at the LLM/tool/graph seams, so it will light up automatically once that integration lands.

## Future Roadmap (High-level)
1. **Evaluation & Security:** Module 22 (evaluation), Module 23 (prompt-injection defense).
2. **Polishing:** Enhancing error handling and telemetry (LangSmith) across the stack.
