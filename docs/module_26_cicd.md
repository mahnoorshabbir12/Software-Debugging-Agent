# Module 26: CI/CD Integration

This module transitions the agent from a reactive local debugger into an autonomous pipeline worker. By integrating it with headless CLIs and GitHub APIs, the agent can be triggered by CI failures, autonomously patch the code, and open Pull Requests for human review.

## 1. Concept

CI/CD integration means giving the agent the ability to interact with version control systems (like GitHub) natively. Instead of a developer pasting an error into a dashboard, a failed GitHub Action or unhandled exception tracker can automatically trigger the agent, which then attempts to fix the bug and submits a PR.

## 2. Problem

An autonomous debugger is only as useful as its delivery mechanism. If developers have to manually run a Python script every time a bug occurs, copy the patch, and manually commit it, the friction is too high. The agent needs to operate where the bugs are found: in the CI/CD pipeline.

## 3. Why this project needs it

To achieve true autonomy, the final output of the debugging process cannot just be a local modified file. It must be a verifiable artifact that fits into existing software engineering workflows—a Pull Request. This allows human engineers to review the AI's logic, see the CI passing, and merge it safely.

## 4. Alternatives & Decisions

### API Integration
- **Local Shell Scripts (`git push`, `gh pr create`):** Works well locally but requires the GitHub CLI (`gh`) to be installed and authenticated in whatever environment it runs in.
- **REST API via HTTP Clients (`requests`):** Requires manually handling authentication, pagination, and JSON schemas for GitHub.
- **Dedicated SDK (`PyGithub`) (chosen):** Provides a clean, typed Python interface for creating branches, pushing commits, and opening PRs.

**Decision:** We chose `PyGithub` as the backing library for our GitHub tool. It is robust, handles the GitHub REST API seamlessly, and integrates natively with standard Personal Access Tokens (PATs).

## 5. Architecture & data flow

```
[CI Failure / GitHub Issue]
        │
        ▼
   ci-run CLI (apps/api/cli.py)
        │
        ▼
  SupervisorGraph ──▶ [Investigate & Patch]
        │
        ▼
  GitHub Tool (sandbox/github_tools.py)
        │
        ▼
[Pull Request Created on GitHub]
```

## 6. Implementation

- `sandbox/github_tools.py` — Contains the `create_pull_request` tool which commits the local changes and uses `PyGithub` to push a branch and open a PR.
- `apps/api/cli.py` — Added a `ci-run` command that takes an issue description and a target repo, triggers the end-to-end `SupervisorGraph`, and ultimately calls the PR creation tool.
- `.env.example` — Added `GITHUB_TOKEN` requirement.

## 7. Verification

- We ensured that `GITHUB_REPOSITORY` is dynamically injected (e.g. from GitHub Actions) rather than hardcoded in `.env`.
- We wrote unit tests for the pipeline execution flow and verified that `create_pull_request` handles missing tokens safely.

## Transferable Rules

> **Use Native SDKs (like PyGithub) when:** integrating agent systems with external platforms (GitHub, Jira, Slack). Do not try to reverse-engineer REST APIs with generic HTTP tools unless absolutely necessary.
>
> **Use CI/CD Agent triggers when:** your project has a high degree of automated testing. The agent can confidently submit a PR knowing the CI will catch any compilation or logic errors before a human reviews it.
