"""
Structured logging setup for the debugging agent.

Concept: structured logging
---------------------------
A normal log line is a string: "agent started for session 5". You cannot query
it. A *structured* log line is a set of key/value fields:

    {"event": "agent.started", "session_id": 5, "level": "info", "ts": "..."}

Now you can filter by session_id, group by event, and feed it to log tooling.

Concept: contextual logging (contextvars)
-----------------------------------------
An investigation touches many functions across many agents. We do not want to
pass `session_id`/`trace_id` into every function just so logs can include them.
`structlog.contextvars` stores context in a Python contextvar; once we bind
`session_id` at the top of a run, *every* log line emitted downstream (even deep
inside an agent) automatically carries it, and it is isolated per async task /
thread.

Concept: the structlog <-> stdlib bridge
----------------------------------------
We route everything through the standard library `logging` module using
structlog's ProcessorFormatter. This means logs produced by libraries (uvicorn,
sqlalchemy, langchain) are rendered with the same JSON/console formatter as our
own structured logs, giving one consistent stream.
"""

from __future__ import annotations

import contextlib
import logging
import sys
from typing import Any, Iterator, Optional

import structlog

from backend.observability.config import ObservabilitySettings, get_observability_settings

# Guard so repeated calls (API startup, CLI, tests) don't stack handlers.
_configured = False


def configure_logging(settings: Optional[ObservabilitySettings] = None) -> None:
    """
    Configure structlog + stdlib logging. Idempotent.

    Call this once at process startup (FastAPI startup event / CLI entry). If a
    logger is requested before this runs, get_logger() will call it lazily.
    """
    global _configured
    settings = settings or get_observability_settings()

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # Processors shared between structlog-native logs and stdlib "foreign" logs.
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,  # inject bound session_id/trace_id
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # structlog produces an event dict, then hands it to the stdlib formatter.
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Choose the final renderer: JSON for machines, colored console for humans.
    if settings.log_json:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    formatter = structlog.stdlib.ProcessorFormatter(
        # foreign_pre_chain runs on records coming from plain stdlib loggers.
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    # Tame the noisiest third-party loggers so our own events stay readable.
    for noisy in ("httpx", "httpcore", "urllib3", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger, configuring logging lazily on first use."""
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)


def bind_log_context(**kwargs: Any) -> None:
    """Bind key/value pairs onto the current context (all later logs include them)."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_log_context() -> None:
    """Remove all bound context (call at the end of a run)."""
    structlog.contextvars.clear_contextvars()


@contextlib.contextmanager
def log_context(**kwargs: Any) -> Iterator[None]:
    """
    Scoped context binding. Values are bound for the duration of the `with`
    block and reset afterwards, so nested runs don't leak context into each other.

        with log_context(session_id=5, trace_id="abc"):
            log.info("agent.started")   # includes session_id + trace_id
    """
    tokens = structlog.contextvars.bind_contextvars(**kwargs)
    try:
        yield
    finally:
        structlog.contextvars.reset_contextvars(**tokens)
