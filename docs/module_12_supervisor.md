# Module 12: Tool-Using Investigation Agent (LangGraph Supervisor)

This module taught us how to orchestrate isolated agents into a cohesive pipeline using a "Graph of Graphs".

## Concepts Learned

### 1. The Supervisor Pattern
**What it is:** A top-level LangGraph state machine that manages the lifecycle of other sub-agents.
**What problem it solves:** Instead of forcing the user to manually trigger Triage, copy the output, trigger Hypothesis, copy the output, and run Evidence loops, the Supervisor autonomously manages the flow.
**Why we used it here:** To fully automate the debugging lifecycle from raw bug report to final evaluated root cause. 
**Where it lives:** `backend/agents/supervisor.py`.

### 2. Graph of Graphs (Sub-graphs)
**What it is:** Invoking one LangGraph application (the `EvidenceGraph`) as a node inside another LangGraph application (the `SupervisorGraph`).
**Why we used it here:** `EvidenceGraph` is highly complex (it loops on tools, evaluates, checks memory). The Supervisor doesn't need to understand tools; it just says, "Here is a hypothesis, go investigate it." By keeping them separate, we maintain clean architectural boundaries.
**How it works:** In `_investigate_node`, the Supervisor invokes `EvidenceGraph.run()`. We pass a namespaced `thread_id` (e.g., `supervisor_thread_0`) so the EvidenceGraph retains its own localized memory while investigating that specific hypothesis.

## Important Decisions & Edge Cases
- **Looping in LangGraph:** We learned that iterating through a list (the `hypotheses` list) in a state machine requires a conditional edge. The node checks the current index, increments it, and the edge routes back to the same node until the index hits the end of the list.
- **Handling Interrupts (Human-in-the-Loop):** Because `EvidenceGraph` is set to pause before tools, invoking it via `app.invoke()` inside a parent node will cause it to return its *paused state* early. In a full production system, we would either add the sub-graph directly as a Node (`workflow.add_node("investigate", evidence_graph.app)`) or manually check if `state.next` is populated to gracefully pause the parent graph as well. 

## Transferable Rules
> **Use the Supervisor Pattern when:** You have distinct, specialized agents (e.g. a Planner, a Coder, a Reviewer) that need to pass structured context to each other in a specific workflow.
> 
> **Use Sub-graphs when:** A specific phase of your workflow (like our tool-calling Evidence loop) is complex and cyclical, but acts as a single logical step to the higher-level orchestrator.
