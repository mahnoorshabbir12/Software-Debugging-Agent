# Module 5: Retrieval as Agent Tools

This document logs our learnings from Module 5, focusing on transitioning our standalone retrieval functions into Agent Tools.

## 1. The Concept of Tool Calling

**What is the concept?**
Tool calling (or Function Calling) is the ability for a Large Language Model (LLM) to output structured JSON data requesting to execute a specific function, rather than just returning raw text. 

For example, without tools, an LLM might say:
> "You should run a search for the word 'JWT_SECRET'."

With tools, the LLM outputs a strictly formatted JSON payload:
```json
{
  "tool": "search_code",
  "args": {
    "query": "JWT_SECRET",
    "top_k": 5
  }
}
```

**What problem does it solve?**
Before tool calling, developers had to write fragile Regular Expressions (Regex) to try and parse an LLM's text output and guess what it wanted to do. Tool calling guarantees a perfectly structured payload that can be directly routed to a Python function.

## 2. Tool Schemas & LangChain

**What is the concept?**
To enable tool calling, the LLM needs to know *what* tools are available. This is done by passing a JSON Schema to the LLM alongside the system prompt.

**How we implemented it:**
We used LangChain's `@tool` decorator (`langchain-core`). 

```python
@tool
def search_code(query: str, path: str = ".", top_k: int = 5) -> str:
    """
    Search the repository for code snippets matching the query...
    """
```

LangChain automatically inspects the Python function's type hints (`query: str`) and its docstring ("Search the repository...") and compiles them into the exact JSON Schema required by models like Llama 3, GPT-4, or Claude. 

**Why docstrings matter:**
In traditional programming, docstrings are for human developers. In Agentic programming, **docstrings are the instructions for the LLM**. If the docstring is vague, the LLM will not know when to use the tool, or it will hallucinate arguments.

## 3. Deterministic vs Agent-Controlled Actions

We have successfully bridged the gap between Modules 1-4 and our final goal.

- **Deterministic (Modules 1-4):** The user types `debugger hybrid-search "RepositoryAnalyzer"`. The CLI executes exactly that one command and returns.
- **Agent-Controlled (Module 5+):** The user types `debugger test-tools "What does the repository look like?"`. The CLI passes this to an LLM. The LLM decides *on its own* that it needs to call `get_repository_map()`, reads the output, and then summarizes it for the user.

We built 4 foundational tools:
1. `get_repository_map`
2. `search_code`
3. `read_file`
4. `list_files`

With these 4 tools, an LLM now has complete read-access to explore and investigate any codebase!

## Next Steps
Now that we have tools, we need a robust framework to manage the Agent's state, handle loops (e.g., search -> read -> search again), and manage memory. We are ready to learn the fundamentals of **LangGraph (Module 6)**.
