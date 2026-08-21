# Module 7: Debugging Triage Agent

This document logs our learnings from Module 7, focusing on how to constrain an LLM to output structured data rather than free-form text.

## 1. The Core Problem: Unstructured Inputs

In an agentic system, the first agent in a chain often receives a messy input from a user. For example:
> *"I upgraded Pydantic and now when I POST to /users, it just returns a 500. Help!"*

If we pass this raw text directly to a Downstream Agent (like a `RepositoryAnalyst`), that agent has to guess what the user meant. Worse, if the downstream agent expects a specific format, the entire system breaks.

## 2. The Solution: Structured Output (Triage Agent)

The **Triage Agent** exists to solve this problem. Its only job is to act as a funnel: it takes messy natural language in, and forces perfectly typed JSON out.

### How it works:
1. **Define a Schema:** We use a Python `pydantic.BaseModel` to strictly define the shape of the data we want.
   ```python
   class InvestigationRequest(BaseModel):
       bug_type: str
       affected_endpoint: Optional[str]
       suspected_area: str
       observed_behavior: str
       expected_behavior: str
   ```
2. **Force the LLM:** We use LangChain's `.with_structured_output()` wrapper. Under the hood, this uses OpenAI's native Tool Calling / JSON Schema features to mathematically constrain the model's output tokens so that they perfectly match our Pydantic model.
3. **Prompt Engineering:** We write a System Prompt that gives the LLM context ("You are a Triage Agent") and instructions on how to fill out the fields (e.g., "Infer the expected behavior if not provided").

## 3. Libraries Used
- **`pydantic`**: Used to define `InvestigationRequest`. Pydantic is the industry standard for Python data validation and is natively understood by LangChain and OpenAI.
- **`langchain-openai`**: Used to initialize the connection to OpenRouter (using Llama 3) and apply the `with_structured_output` modifier.

## Next Steps
Now that we have a structured `InvestigationRequest`, we can pass this JSON payload to the next agent in our architecture: the **Hypothesis-Driven Debugging Agent** (Module 8).
