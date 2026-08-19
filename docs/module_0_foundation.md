# Module 0: Project Setup & Engineering Foundation

## What we built
We created a clean Python project structure for the Autonomous Software Debugging Agent before introducing any AI concepts. We established a foundational CLI, test suite, and project configuration.

## Concepts learned

### Python Project Structure (`src/` and `tests/`)
**What:** Organizing code into clearly defined folders where `src/` holds application code and `tests/` holds test suites.
**Why:** Prevents pollution of the root directory and makes it explicit where application logic vs. tests reside. It also solves import path ambiguities when testing.
**Where we used it:** Created `src/` and `tests/` directories.

### Dependency Management (`pyproject.toml`)
**What:** The modern standard for Python project configuration, replacing `setup.py` and `requirements.txt`.
**Why:** It centralizes project metadata, dependencies, script entry points, and tool configurations (like `pytest` and `black`) into a single file.
**Where we used it:** Created `pyproject.toml` at the project root.

### Environment Variables (`.env.example`)
**What:** A file for managing configuration parameters and secrets injected as environment variables.
**Why:** Separates code from configuration. We never hardcode API keys or environment-specific URLs in the source code.
**Where we used it:** Created `.env.example`.

### CLI Creation (`typer`)
**What:** A library for building Command Line Interfaces based on Python type hints.
**Why:** It provides an easy, declarative way to expose agent functionality to the user via terminal commands.
**Where we used it:** Created `src/cli.py` with an `investigate` command.

### Automated Tests (`pytest` & `CliRunner`)
**What:** Writing reproducible scripts that verify if our application code behaves as expected.
**Why:** Manual testing does not scale. Automated tests ensure that as we build new modules, we don't break existing ones.
**Where we used it:** `tests/test_cli.py` verifies our CLI command executes without errors.

## Important decisions

### Decision: Python Project Manager
**Options:**
- `pip` + `requirements.txt`
- `Poetry`
- Standard `pyproject.toml` with `setuptools`

**Recommendation:** Standard `pyproject.toml` with `setuptools`
**Why this project should use it:** It's the standard, lightweight, built-in approach for Python. It minimizes external tooling dependencies while still providing all the modern features needed (like optional dependencies and CLI scripts).

## Transferable rules

> **Use this when:** Starting a new Python project. Always begin with a structural foundation before writing complex logic.
> 
> **Avoid/reconsider when:** Writing a single throwaway script for personal use.
> 
> **In this project:** This structure will be the bedrock that allows us to safely integrate AI agents, LangGraph, and Vector Databases in the upcoming modules.
