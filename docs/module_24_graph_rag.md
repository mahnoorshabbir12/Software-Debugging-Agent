# Module 24: Graph RAG (Neo4j)

This module replaces our reliance on pure semantic search with structural, graph-based code intelligence. By parsing the repository into an Abstract Syntax Tree (AST) and loading it into Neo4j, the agent can answer deterministic questions about code structure.

## 1. Concept

Graph RAG extends Retrieval-Augmented Generation by representing knowledge as nodes and edges rather than flat text embeddings. In software engineering, code is inherently a graph:
- **Nodes**: Files, Classes, Functions, Methods
- **Edges**: `IMPORTS`, `CALLS`, `INHERITS_FROM`, `CONTAINS`

## 2. Problem

Vector search (Module 4) is excellent for fuzzy concepts ("find authentication logic"). However, it is terrible at structural questions:
- "What functions call `verify_token()`?"
- "Which classes inherit from `BaseModel`?"
Vector databases do not understand relationships, leading the agent to hallucinate or miss critical context when tracing execution flow.

## 3. Why this project needs it

When an autonomous debugger investigates a stack trace, it must definitively follow the control flow up the call stack or down into dependencies. If it only uses vector search, it guesses the relationships based on keyword proximity. A graph database provides deterministic, 100% accurate relationship traversal.

## 4. Alternatives & Decisions

### Knowledge Store
- **Semantic Vector DB (Qdrant):** Good for concepts, bad for structure.
- **LSP / Language Servers:** Real-time, accurate, but hard to query historically or globally without a running server instance per language.
- **Graph Database (Neo4j) (chosen):** Persists the AST globally, supports rich Cypher queries, and is language-agnostic at the schema level.

**Decision:** We chose a local Neo4j container. It allows the agent to issue Cypher queries to explore the codebase structurally without incurring cloud costs or relying on external services.

## 5. Architecture & data flow

```
Source Code
    │
    ▼
AST Parser (Python `ast` module)
    │
    ▼
Graph Builder ───▶ Nodes (Function, Class, File)
    │          │
    │          └──▶ Edges (CALLS, IMPORTS)
    ▼
Neo4j Database
    │
    ▼
Graph Tools (LangChain Tools)
    │
    ▼
CodeAgent (Multi-Agent framework)
```

## 6. Implementation

- `ingestion/graph_builder.py` — The AST parser and ingestion script that connects to Neo4j and executes `MERGE` Cypher queries to build the graph.
- `sandbox/graph_tools.py` — Agent-facing tools (`get_function_dependencies`, `get_callers`, `get_file_structure`) that wrap Cypher queries into structured LLM outputs.
- `docker-compose.yml` — Updated to include a local Neo4j instance.

## 7. Verification

- We successfully parsed the project's own backend files.
- We verified the `get_callers` tool correctly returned the exact callers of a specific function using Cypher traversal `()-[:CALLS]->()`.

## Transferable Rules

> **Use Vector Databases when:** you are searching for concepts, domain logic, or fuzzy semantics ("how do we handle rate limits?").
>
> **Use Graph Databases when:** you are tracing control flow, computing dependencies, or need 100% accurate structural relationships ("what files import this module?").
