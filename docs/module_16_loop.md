# Module 16: Self-Correction Loop

This module wires our isolated tools (Investigation, Patching, Validation) into a cohesive autonomous loop managed by the LangGraph orchestrator.

## Concepts Learned

### 1. Conditional Edges for Looping
**What it is:** In LangGraph, a node doesn't have to statically point to a single next node. We can use conditional edges to route the graph dynamically based on the state.
**What problem it solves:** A linear DAG (Directed Acyclic Graph) is insufficient for debugging, because fixing a bug requires trial and error. If a fix fails, we must go back and try again.
**Why we used it here:** We added a `_route_validation` edge after the `validate` node. If `validation_result.passed` is True, the graph ends successfully. If it is False, the graph loops back to the `patch` node.

### 2. Bounded Loops (Circuit Breakers)
**What it is:** A counter that prevents an infinite loop.
**What problem it solves:** LLMs can get stuck in "hallucination loops", repeatedly trying the exact same incorrect fix, failing validation, and retrying forever. This burns tokens and time.
**Why we used it here:** We added `patch_attempts` to the `SupervisorState`. If the validation fails 3 times, the `_route_validation` edge routes to a `discard_hypothesis` node, which discards the current hypothesis and moves to the *next* hypothesis generated during triage.

### 3. Context Injection (Learning from Mistakes)
**What it is:** Passing the failure logs from the environment directly back to the LLM.
**What problem it solves:** An LLM cannot fix its mistake if it doesn't know *why* it failed. "It didn't work" is not enough information. "It failed on line 42 with TypeError: expected string, got int" allows the LLM to instantly realize its mistake.
**Why we used it here:** We collect the `lint_output`, `type_output`, and `test_output` from the Sandbox Validator and pass them directly into the `PatchAgent`'s system prompt as `previous_failures`.

## Transferable Rules
> **Implement Circuit Breakers:** Always bound your autonomous loops. Use a `max_iterations` counter and build an escape hatch (e.g., trying a different hypothesis) when the limit is reached.
> 
> **Feed Back the Errors:** When an LLM action fails, never just tell it to "try again". Always pipe the exact raw stdout/stderr from the environment back into its prompt. LLMs are exceptional at diagnosing their own mistakes when given the stack trace.
