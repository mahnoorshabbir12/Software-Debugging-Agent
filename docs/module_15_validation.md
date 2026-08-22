# Module 15: Automated Validation

This module connects the Patch Generation phase with the Docker Sandbox phase to create a fully autonomous "CI/CD pipeline in a box".

## Concepts Learned

### 1. Temporary Workspaces
**What it is:** Instead of applying LLM patches directly to the user's live codebase, we copy the project to a temporary directory (`tempfile.TemporaryDirectory()`). 
**What problem it solves:** Applying untested patches directly to a live repository is dangerous and messy. If the patch breaks things, rolling it back can be complicated.
**Why we used it here:** By copying the code to a temporary directory first, applying the patch, and then mounting that temp directory into our Docker sandbox, we ensure the user's workspace remains completely pristine until the patch is formally validated.

### 2. Multi-stage Validation
**What it is:** Running multiple distinct checks on code (Linting, Static Type Checking, and Unit Tests).
**What problem it solves:** An LLM might output code that passes tests but introduces severe syntax errors, undefined variables, or type mismatches. 
**Why we used it here:** We used three specific tools:
- **Ruff:** For extremely fast linting and syntax checking.
- **Mypy:** For static type checking to ensure the LLM didn't pass strings into integer functions.
- **Pytest:** To ensure the behavioral logic of the bug is actually fixed.

## Transferable Rules
> **Fail Fast:** Always run validation checks in order of speed and strictness. Run Linters first (Ruff), then Type Checkers (Mypy), and finally Unit Tests (Pytest). If linting fails, don't waste time running the test suite.
> 
> **Never Validate in Production:** Always validate generated code in a completely isolated, temporary environment before presenting it to the user.
