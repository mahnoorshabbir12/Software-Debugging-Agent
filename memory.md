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

## Current Module Plan
- **Module 18 - Final Integration:** Building a FastAPI backend and React frontend to provide a rich UI for developers to interact with the agent and view its persistent state.

## Future Roadmap (High-level)
1. **Polishing:** Enhancing error handling and telemetry (LangSmith) across the stack.
