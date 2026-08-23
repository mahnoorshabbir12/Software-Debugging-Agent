# Module 18: FastAPI Backend

In this module, we transitioned the autonomous debugging agent from a purely CLI-driven tool into a REST API application using FastAPI.

## Concepts Learned

### 1. API Structure
**What it is:** Exposing the agent's core functionalities (creating investigations, fetching hypotheses, validating patches) over HTTP.
**What problem it solves:** A CLI is great for local execution, but an autonomous agent usually runs in the cloud. We need a way for a user interface (like the React dashboard in Module 20) or CI/CD pipelines (Module 26) to interact with it programmatically.
**Why we used it here:** FastAPI provides automatic OpenAPI generation (Swagger), very fast performance, and built-in validation using Pydantic, which perfectly matches our existing use of Pydantic and SQLModel.

### 2. Decoupling Schemas and Models
**What it is:** Separating the API request/response format (Pydantic `BaseModel`) from the database format (`SQLModel`).
**What problem it solves:** Returning raw database rows over an API can leak internal fields, and accepting raw database rows allows clients to modify fields they shouldn't (like `id` or `created_at`). 
**Why we used it here:** We defined `InvestigationCreate`, `RepositoryResponse`, etc., in `schemas.py`. The API router receives `InvestigationCreate` and translates it into a SQLModel `Investigation` object. This creates a clean boundary.

### 3. Dependency Injection (DI)
**What it is:** A design pattern where an object or function receives other objects it depends on, rather than creating them itself.
**What problem it solves:** Managing resources like database sessions is tedious and error-prone if done manually in every endpoint. You have to remember to open, close, and handle exceptions every time.
**Why we used it here:** We used FastAPI's `Depends(get_session)` to automatically inject a database session into our endpoints. FastAPI ensures the session is properly closed after the request is complete.

## Transferable Rules
> **Schema Boundaries:** Always create dedicated Pydantic schemas for API inputs and outputs. Do not blindly return database ORM objects directly to the client unless you are absolutely sure of the boundaries.
>
> **Inject Resources:** Use FastAPI's Dependency Injection system for shared resources like database connections, authentication tokens, and configuration. It drastically reduces boilerplate and makes testing easier.
