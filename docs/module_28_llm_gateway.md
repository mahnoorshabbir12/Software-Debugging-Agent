# Module 28: LLM Gateway (LiteLLM Proxy)

This module introduces an LLM Gateway between the application and LLM providers, giving us provider failover, model aliasing, and gateway-level caching without changing any agent logic.

## 1. Concept

An **LLM Gateway** is a reverse-proxy specialized for AI model APIs. Instead of every agent calling OpenRouter directly, all LLM traffic flows through a local proxy (LiteLLM) that decides which real provider to forward each request to.

**Mental model:** Think of it like NGINX or an API gateway, but purpose-built for LLM calls. Your application talks to one URL (`localhost:4000/v1`), and the gateway handles routing, retries, failover, and caching behind the scenes.

## 2. Problem

Before this module:
- If OpenRouter returned a `503 Service Unavailable`, every agent crashed (even though Module 27 added client-side retries, there was no fallback to a *different provider*).
- Switching from OpenRouter to direct OpenAI or local Ollama required editing Python code and redeploying.
- The model name `meta-llama/llama-3.1-8b-instruct` was hardcoded in every agent constructor, creating 5 places to update when changing models.
- The `InMemoryCache` only cached within a single process; multiple workers couldn't share cached responses.

## 3. Why this project needs it

Autonomous agents run unattended (e.g., in CI or overnight). They must gracefully survive provider outages without human intervention. Additionally, during development we want to swap freely between remote APIs (OpenRouter, OpenAI) and local inference (Ollama) without touching application code.

## 4. Alternatives & Decisions

### Gateway vs. Direct Client Factory

| Approach | What it means | Pros | Cons | Best when |
|---|---|---|---|---|
| Direct Factory (`build_llm()` → OpenRouter) | Application code configures the SDK client directly | Zero infrastructure, simple testing | No cross-provider failover, no shared cache | Single provider, solo dev |
| LiteLLM Proxy (chosen) | Lightweight Docker sidecar that proxies LLM calls | Automatic failover, model aliasing, gateway cache, virtual keys | Extra Docker container to run | Multi-provider, production, team environments |
| Portkey / Cloudflare AI Gateway | Managed hosted gateway | No self-hosting, enterprise features | Vendor lock-in, network latency to hosted gateway | Enterprise SaaS at scale |

**Decision:** LiteLLM Proxy. It's open-source, runs locally as a Docker container alongside our existing `docker-compose.yml`, and provides the exact features we need (failover, aliasing, caching) with minimal complexity.

### Caching Strategy: L1 + L2

| Layer | Implementation | Scope | Speed |
|---|---|---|---|
| L1 (in-process) | LangChain `InMemoryCache` | Single Python process | ~0ms (memory) |
| L2 (gateway) | LiteLLM `cache: true` | All workers/processes | ~1-5ms (network to proxy) |

**Decision:** Keep both layers. L1 catches repeated calls within a single agent run instantly. L2 catches identical prompts across concurrent API workers or successive runs.

## 5. Architecture & Data Flow

```
Before (Module 27):
  Agent → build_llm() → ChatOpenAI(openrouter.ai) → OpenRouter → Llama 3.1

After (Module 28):
  Agent → build_llm() → ChatOpenAI(localhost:4000) → LiteLLM Proxy
                                                         ├→ OpenRouter (primary)
                                                         └→ Ollama (fallback)
```

### How the gateway resolves a request

1. Agent calls `build_llm()` which creates a `ChatOpenAI` pointing at `http://localhost:4000/v1`.
2. The agent sends a request for model `debugger/main-model` (a virtual alias).
3. LiteLLM Proxy looks up `debugger/main-model` in `litellm_config.yaml` and finds two deployments: OpenRouter and Ollama.
4. The proxy tries OpenRouter first (primary). If it succeeds → return response.
5. If OpenRouter fails (timeout, 503, rate limit) → the proxy automatically retries against Ollama (fallback).
6. The response flows back through the same path to the agent.

The existing `TracingCallbackHandler` still captures all spans correctly because it hooks into LangChain's callback system, which is independent of the network layer.

## 6. Implementation

### Infrastructure
- **`litellm_config.yaml`** — Gateway routing config: model aliases, provider deployments, fallback rules, caching settings.
- **`docker-compose.yml`** — Added `litellm` service running the proxy on port 4000.
- **`.env` / `.env.example`** — New variables: `LITELLM_BASE_URL`, `LITELLM_API_KEY`, `LITELLM_MASTER_KEY`, `LLM_MODEL_NAME`.

### Application Code
- **`backend/llm.py`** — `build_llm()` now reads `LITELLM_BASE_URL` and `LITELLM_API_KEY` instead of `OPENROUTER_BASE_URL` and `OPENROUTER_API_KEY`. `DEFAULT_MODEL` reads from `LLM_MODEL_NAME` env var (default: `debugger/main-model`).
- **`backend/agents/{triage,hypothesis,evidence,patch}.py`** — Default `model_name` parameter changed from hardcoded `"meta-llama/llama-3.1-8b-instruct"` to `None`, letting `build_llm()` resolve from the environment.
- **`sandbox/graph_experiments.py`** — Replaced inline `ChatOpenAI` calls with `build_llm()`.
- **`apps/api/cli.py`** — Preflight guards changed from `OPENROUTER_API_KEY` to `LITELLM_API_KEY`.
- **`backend/observability/metrics.py`** — Comment updated to reflect gateway-agnostic pricing.

## 7. Key Concept: Why the Factory Pattern Made This Safe

The entire gateway integration required changing **one function** (`build_llm()`) and updating agent constructor defaults. No agent logic, prompt templates, tool definitions, graph structure, or observability code changed.

This is the power of the factory pattern combined with the single-responsibility principle:
- `build_llm()` owns *how* to connect to an LLM.
- Agents own *what* to ask the LLM.
- The observability layer owns *how* to observe the LLM.

When we changed the *how* (OpenRouter → LiteLLM Proxy), the *what* and *observe* layers were untouched.

## 8. Verification

- LiteLLM Proxy starts via `docker compose up litellm` and responds to health checks at `http://localhost:4000/health`.
- Direct curl test against the gateway confirms model routing works.
- Existing unit tests pass unchanged (they mock LLM calls at a level above the transport).
- End-to-end CLI test (`debugger triage "..."`) confirms agents route through the gateway.

## Transferable Rules

> **Use an LLM Gateway when:** you need multi-provider failover, want to swap models/providers without redeploying, or run multiple workers that benefit from shared caching.
>
> **Avoid/reconsider when:** you only use a single provider, run locally for solo development, and don't need failover. A simple factory function is sufficient.
>
> **Use model aliasing when:** you want to decouple your application code from provider-specific model identifiers. Virtual names (`debugger/main-model`) let you change the real model via config without touching code.
>
> **Use layered caching (L1 + L2) when:** you have both in-process repeated calls (agent loops) AND cross-process duplication (multiple API workers). L1 is instant; L2 is shared.
