# Module 8: Hypothesis-Driven Debugging

This document logs our learnings from Module 8, focusing on Divergent Thinking and how it applies to AI Agents.

## 1. The Core Problem: Premature Convergence

When an LLM is presented with a problem (e.g., "Why does POST /users return 500?"), its default behavior is **Convergent Thinking**. It tries to immediately calculate the single, most statistically probable answer and spits it out. 

In a debugging context, this is dangerous. If the LLM guesses "The database is down", it will obsessively search the codebase for database connection strings and ignore the fact that the issue was actually a Pydantic version upgrade. This leads to endless rabbit holes and hallucination.

## 2. The Solution: Divergent Thinking (Hypothesis Agent)

To fix this, we force the LLM into a state of **Divergent Thinking** before it is allowed to search the code.

We created the `HypothesisAgent`. Its job is to take the structured `InvestigationRequest` from the Triage Agent and brainstorm multiple *competing* theories about what went wrong.

### The Schema
We constrain this brainstorming process using Pydantic:
```python
class Hypothesis(BaseModel):
    title: str
    description: str
    reason: str
    expected_evidence: List[str]
    investigation_plan: List[str]
```

By forcing the LLM to write down the `expected_evidence` (e.g., "I expect to find a `requirements.txt` file showing pydantic >= 2.0") and an `investigation_plan`, we are teaching the agent to act like a scientist.

## Next Steps

Now that we have a list of competing hypotheses, we can move to Module 9, where we will build an agent that executes the `investigation_plan` and searches the codebase for the `expected_evidence` to see which hypothesis is actually true.
