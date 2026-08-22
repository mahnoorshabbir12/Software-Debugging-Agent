# Module 10: Git Investigation Tools

This module implements Git history and investigation tools for the debugging agent. Providing historical context to the agent allows it to understand how code evolved and precisely when regressions or bugs were introduced.

## Core Concepts

The agent accesses Git through a set of read-only LangChain tools that securely execute shell commands via Python's `subprocess`.

- **History**: Fetching commit history (`git log`).
- **Diffing**: Identifying what changed between specific commits or what is modified in the working tree (`git diff`).
- **Commit Details**: Reviewing changes made in a specific commit (`git show`).
- **Attribution**: Finding out when specific lines were last modified and by whom (`git blame`).
- **Searching**: Looking up specific keywords in the commit history (`git log -S`).

## Tools Implemented

These tools are added to the `sandbox/tools.py` and exported through `AGENT_TOOLS`:

- `git_log`
- `git_diff`
- `git_show`
- `git_blame`
- `search_commits`

## Output Management

Since Git commands like `git diff` or `git blame` can output thousands of lines, a truncation mechanism is employed. Outputs exceeding a reasonable limit (e.g., 500 or 1000 lines) are automatically truncated with a note indicating the total number of lines. This ensures the LLM's context window isn't inadvertently flooded, which could cause token limit errors or distract the agent from the core issue.
