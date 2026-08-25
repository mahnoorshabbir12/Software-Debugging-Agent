# Module 25: Multi-Agent Architecture

This module fractures our single monolithic "God Agent" into a network of specialized sub-agents, coordinated by a central Orchestrator. By giving each sub-agent a narrow focus and limited toolset, we drastically improve reasoning reliability and reduce tool-selection hallucinations.

## 1. Concept

Multi-Agent orchestration involves combining multiple specialized LLMs (or the same LLM with different system prompts) to solve a complex task. Instead of one agent deciding between 25 tools, a Supervisor routes tasks to a `CodeAgent` (with 5 code tools), a `GitAgent` (with 5 Git tools), or a `ResearchAgent` (with 5 web tools).

## 2. Problem

As we added Vector RAG, Graph RAG, Git tools, Web tools, and file editing tools, our central `EvidenceAgent` accumulated too many responsibilities. 
When an LLM is presented with 20+ tools and a generic prompt ("You are a debugging assistant"), its context window becomes diluted. It struggles to choose the right tool, hallucinates arguments, or gets stuck using the wrong approach (e.g., trying to read Git history via file reading).

## 3. Why this project needs it

Software debugging requires highly distinct modes of thinking:
- **Code Mode**: Exploring ASTs, reading files, understanding syntax.
- **Git Mode**: Exploring time, reading diffs, finding regressions.
- **Web Mode**: Exploring documentation, GitHub issues, finding external context.
Separating these concerns prevents the agent from conflating them and allows us to provide hyper-specific system prompts for each mode.

## 4. Alternatives & Decisions

### Orchestration Pattern
- **Hierarchical/Network:** Agents can talk directly to each other (e.g., CodeAgent asks GitAgent for help).
- **Flat Routing / Supervisor (chosen):** A central Orchestrator acts as a router. Agents only talk to the Orchestrator, not to each other.

**Decision:** We chose a **Flat Graph with Routing**. A flat hierarchy is vastly easier to debug, control, and trace. It prevents runaway "agent chat" loops where two sub-agents infinitely argue with each other.

## 5. Architecture & data flow

```
User / Hypothesis
       │
       ▼
  Orchestrator Node (LLM with structured output)
       │
       ├───▶ (Task: "Find file history") ───▶ GitAgent ──▶ [Git Tools]
       │
       ├───▶ (Task: "Trace AST callers") ───▶ CodeAgent ─▶ [Graph/Vector Tools]
       │
       └───▶ (Task: "Search Pandas docs") ──▶ WebAgent ──▶ [Web Tools]
```

## 6. Implementation

- `backend/agents/sub_agents.py` — Defines the personas (`CodeAgent`, `GitAgent`, `ResearchAgent`) using LangGraph's `create_react_agent`.
- `backend/agents/evidence.py` — Refactored to act as the `Orchestrator`. It evaluates the current hypothesis and uses `llm.with_structured_output` to select which sub-agent to invoke.
- `tests/test_multi_agent.py` — Unit tests verifying the orchestrator correctly routes tasks to the appropriate sub-agent based on the input text.

## 7. Verification

- We successfully ran tests showing the Orchestrator routing a Git-related query to the `GitAgent` and an AST-related query to the `CodeAgent`.
- We ensured that sub-graphs correctly update the parent state and return control to the Orchestrator after their execution.

## Transferable Rules

> **Use a Single Agent when:** your task requires fewer than ~5-7 tools and a single cohesive mode of reasoning (e.g., a simple code editor).
>
> **Use Multi-Agent Orchestration when:** the total number of tools overwhelms the context window, or when the task requires radically different personas and strict separation of concerns.
