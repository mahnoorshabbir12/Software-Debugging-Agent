"""
Metrics: cost estimation and span aggregation.

Concept: metrics vs traces
--------------------------
A trace answers "what happened, step by step". A *metric* answers "how much" in
aggregate: total tokens, total cost, total latency, error counts. This module
turns raw token counts into cost, and a list of spans into a summary.

Cost model
----------
LLM providers bill per token, at different rates for input (prompt) and output
(completion) tokens. We keep a small price table (USD per 1,000,000 tokens) and
compute cost = prompt/1e6*in_price + completion/1e6*out_price.

The prices are approximate and easy to update; unknown models return None so we
never fabricate a number.
"""

from __future__ import annotations

from typing import Iterable, Optional

from backend.observability.logging import get_logger

log = get_logger("observability.metrics")

# USD per 1,000,000 tokens: model -> (input_price, output_price).
# Approximate vendor list prices. These apply regardless of whether calls go
# through the LiteLLM gateway or directly to a provider. Adjust as needed.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "meta-llama/llama-3.1-8b-instruct": (0.02, 0.03),
    "meta-llama/llama-3.1-70b-instruct": (0.35, 0.40),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),
}


def _lookup_prices(model: Optional[str]) -> Optional[tuple[float, float]]:
    if not model:
        return None
    if model in MODEL_PRICES:
        return MODEL_PRICES[model]
    # Lenient suffix/contains match so "…/llama-3.1-8b-instruct:free" still maps.
    for key, prices in MODEL_PRICES.items():
        if key in model or model in key:
            return prices
    return None


def estimate_cost(
    model: Optional[str],
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
) -> Optional[float]:
    """
    Estimate USD cost for an LLM call. Returns None for unknown models so callers
    can distinguish "free/unknown" from "zero cost".
    """
    prices = _lookup_prices(model)
    if prices is None:
        return None
    in_price, out_price = prices
    cost = (prompt_tokens or 0) / 1_000_000 * in_price
    cost += (completion_tokens or 0) / 1_000_000 * out_price
    return round(cost, 8)


def summarize_spans(spans: Iterable) -> dict:
    """
    Aggregate a collection of SpanEvent-like objects (must expose .kind, .status,
    .total_tokens, .prompt_tokens, .completion_tokens, .cost_usd, .duration_ms)
    into a metrics dictionary. Pure function: no DB access, easy to unit test.
    """
    summary = {
        "llm_calls": 0,
        "tool_calls": 0,
        "node_transitions": 0,
        "errors": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "total_duration_ms": 0.0,
        "llm_duration_ms": 0.0,
    }
    for s in spans:
        if s.status == "error":
            summary["errors"] += 1
        if s.kind == "llm":
            summary["llm_calls"] += 1
            summary["prompt_tokens"] += s.prompt_tokens or 0
            summary["completion_tokens"] += s.completion_tokens or 0
            summary["total_tokens"] += s.total_tokens or 0
            summary["total_cost_usd"] += s.cost_usd or 0.0
            summary["llm_duration_ms"] += s.duration_ms or 0.0
        elif s.kind == "tool":
            summary["tool_calls"] += 1
        elif s.kind == "chain":
            summary["node_transitions"] += 1
        summary["total_duration_ms"] += s.duration_ms or 0.0

    summary["total_cost_usd"] = round(summary["total_cost_usd"], 8)
    summary["total_duration_ms"] = round(summary["total_duration_ms"], 2)
    summary["llm_duration_ms"] = round(summary["llm_duration_ms"], 2)
    return summary
