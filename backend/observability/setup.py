"""
Observability bootstrap.

A single entry point that wires the observability layer together:
  1. configures structured logging
  2. registers the span sinks (database now; SSE is added in Stage 4)

Call init_observability() once at process startup (FastAPI startup / CLI).
It is idempotent, so calling it more than once is harmless.
"""

from __future__ import annotations

from backend.observability.logging import configure_logging, get_logger
from backend.observability.spans import register_sink

_initialized = False


def init_observability() -> None:
    global _initialized
    configure_logging()
    if _initialized:
        return

    # Imported lazily so heavy deps (DB engine, event dispatcher) are only
    # pulled in when observability boots.
    from backend.observability.store import database_sink
    from backend.observability.streaming import sse_sink

    register_sink(database_sink)  # persist every span
    register_sink(sse_sink)       # stream every span to the browser live
    _initialized = True

    get_logger("observability.setup").info("observability.initialized")
