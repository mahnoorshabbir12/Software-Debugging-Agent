# Module 17: Persistent Agent State & Memory

In this module, we transitioned the agent's memory from ephemeral RAM to a persistent PostgreSQL database.

## Concepts Learned

### 1. Persistent State (Long-term Memory)
**What it is:** Storing the outputs and context of an agent's run into a durable database (PostgreSQL).
**What problem it solves:** Agent runs can take a long time (minutes or even hours). If the server restarts, or if the user wants to check in on a past debugging session, in-memory state is completely lost.
**Why we used it here:** By persisting the `Investigation`, `Hypothesis`, `Evidence`, `Patch`, and `TestRun` records to Postgres, we guarantee that the state survives restarts. Furthermore, it allows us to build a UI (in Module 18) that can query and display these records cleanly.

### 2. SQLModel & Alembic
**What it is:** `SQLModel` is an ORM (Object Relational Mapper) that combines SQLAlchemy and Pydantic. `Alembic` is a database migration tool.
**What problem it solves:** Writing raw SQL strings is error-prone. Managing schema changes manually (e.g. adding a new column) across different environments is impossible without version control.
**Why we used it here:** We used SQLModel to define our tables exactly as Python classes (with types), and we used Alembic to auto-generate the SQL migration scripts (`alembic revision --autogenerate`) to build the Postgres tables.

### 3. Side-Effects in Graph Nodes
**What it is:** Triggering external actions (like database writes) directly from within the nodes of a StateGraph.
**What problem it solves:** LangGraph's internal checkpointer (`MemorySaver` or `PostgresSaver`) stores the exact internal dictionary of the state, but it stores it as a binary blob. We want to store *structured* data (like a specific "Hypothesis" table row) so a frontend can query it.
**Why we used it here:** Inside `_triage_node`, `_hypothesis_node`, `_patch_node`, and `_validate_node`, we open a database session and `session.add()` the generated models. This synchronizes the agent's internal progress into our structured database.

## Transferable Rules
> **Durable by Default:** Always build your agentic systems with a persistent database (PostgreSQL/SQLite) if the task takes longer than 30 seconds. Users hate losing progress.
>
> **Separate Internal State from Business Data:** Do not rely purely on an agent framework's internal checkpointer for your application's data layer. Build proper relational tables for the domain concepts (like "Patches" or "TestRuns") so other services (like a UI or API) can query them normally without understanding the agent framework's binary blob formats.
