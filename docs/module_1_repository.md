# Module 1: Repository Understanding

This document logs our learnings from Module 1, where we built the ability to ingest and understand an unfamiliar repository, identifying its structure before proceeding to code parsing.

## 1. Monorepo vs Standard Layout

**What it is:** A monorepo is a single repository containing multiple distinct projects or packages (e.g., a React frontend and a FastAPI backend in one git repo). A standard layout contains only one main project.

**Why we care:** Our tool (`RepositoryAnalyzer`) needs to dynamically adapt to what it is scanning. We can't assume every repository is a simple Python backend. We use dependency files (`pyproject.toml`, `package.json`) placed inside depth-1 subdirectories as a heuristic to detect distinct "sub-projects".

**Where it is used:** `ingestion/scanner.py` uses this heuristic to populate `SubProjectMap` objects.

## 2. Directory Traversal and Ignore Rules (`pathspec`)

**What it is:** The process of walking a directory tree (`os.walk`) while adhering to rules (like `.gitignore`) that dictate which files to skip.

**Why we care:** Blindly indexing a software repository is disastrous. Directories like `node_modules`, `__pycache__`, or `.venv` can contain tens of thousands of irrelevant files that would overwhelm our LangGraph agents and cost unnecessary tokens. We use the `pathspec` library because it accurately parses git wildcard match syntax, preventing us from indexing junk.

**Where it is used:** In `ingestion/scanner.py`'s `_load_ignore_patterns` and `_is_ignored` methods.

## 3. Pydantic Domain Models

**What it is:** Pydantic is a data validation library that forces type hints at runtime. We use it to strictly define the shape of our data.

**Why we care:** Our `RepositoryMap` acts as the first piece of "evidence" collected about a repository. By strictly defining its shape using `BaseModel`, we ensure that later down the line, when we pass this state into our LangGraph debugging graph, the AI agents receive a guaranteed JSON schema without missing fields.

**Where it is used:** `ingestion/models.py`.

## Next Steps
Now that the system can map out *where* the code is and *what* it consists of structurally, we can move on to **Module 2: Code Parsing & Structural Chunking**, where we will actually start reading the code blocks using AST tools rather than simple text splitters.
