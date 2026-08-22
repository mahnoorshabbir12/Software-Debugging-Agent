# Module 9: Evidence Collection & Hypothesis Evaluation

This document logs our learnings from Module 9, focusing on how we use Tools within a LangGraph StateMachine to gather evidence and prevent AI hallucination.

## 1. The Core Problem: LLM Hallucination
If you ask an LLM if a hypothesis is true, it will often confidently guess "Yes", because its training data pushes it to provide an answer. It rarely stops to say "I don't know."

## 2. The Solution: Evidence Grounding
To solve this, we built the **EvidenceGraph**. It has two distinct phases:

### Phase 1: Tool Execution (`investigate` node)
Instead of asking the LLM to guess, we give it the tools we built in Module 5 (e.g., `search_code`, `read_file`). We pass it the `investigation_plan` and tell it to use the tools to search the actual codebase.
Because this is built in LangGraph, if a search returns empty results, the agent doesn't crash; it simply loops back, decides to try a different search term, and calls the tool again.

### Phase 2: Evaluation (`evaluate` node)
Once the LLM decides it has gathered enough evidence (or hits our safety cutoff of 3 loops), the graph transitions to the Evaluation node.
Here, we force the LLM into a structured Pydantic schema:
```python
class Evaluation(BaseModel):
    status: Literal["SUPPORTED", "REJECTED", "UNCERTAIN"]
    confidence_score: int
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
```

### The Power of "UNCERTAIN"
By explicitly giving the LLM the `UNCERTAIN` option in our literal types, and instructing it in the prompt ("If you didn't find strong evidence either way, choose UNCERTAIN"), we dramatically reduce hallucination. The LLM is no longer forced to guess; it can safely admit it needs more information.

## 3. Stateful Graph Execution with MemorySaver

To make our agent loop safe and pause-able, we integrated LangGraph's `MemorySaver`.

**What is it?**
`MemorySaver` is a checkpointer that persists the graph's state (the `EvidenceState`) at every node execution. It allows the graph to remember its history across sessions and pause execution mid-flight.

**Why we need it here:**
While our current tools are read-only (`search_code`), future modules will introduce destructive tools (like writing files or modifying git history). By using `MemorySaver` combined with `interrupt_before=["tools"]` when compiling the graph, we create a **Human-in-the-Loop** checkpoint. The agent will automatically pause and ask for human permission before running any tool, preventing disastrous autonomous actions.

**Where it lives:**
It is initialized in `backend/agents/evidence.py` and passed into `workflow.compile(checkpointer=self.memory, interrupt_before=["tools"])`. When we run the graph, we pass a `thread_id` to uniquely identify the session's memory.

## Next Steps
Now that the agent can retrieve code to prove its hypotheses, we need to give it historical context. In **Module 10**, we will add Git tools so the agent can check *when* a bug was introduced.
