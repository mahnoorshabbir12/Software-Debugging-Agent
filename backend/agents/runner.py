"""
Background runner for a debug session.

This module provides the function that FastAPI's BackgroundTasks will execute.
It steps through the investigation pipeline, updates the database, and emits
SSE events so the frontend timeline updates in real time.

For now this is a simulation of the real LangGraph pipeline — it walks through
each investigation step with realistic delays. When the real agents (triage,
hypothesis, evidence, patch) are wired in, this runner will call them instead.
"""

import time
import asyncio
from datetime import datetime
from sqlmodel import Session

from backend.database.core import engine
from backend.database.models import DebugSession
from backend.agents.controller import AgentController, AgentCancelledException
from backend.agents.events import EventDispatcher


# The ordered steps the agent walks through
INVESTIGATION_STEPS = [
    ("initializing",        "Initializing debug session...",              2),
    ("parsing_error",       "Parsing error details from bug report...",   3),
    ("inspecting_repository","Scanning repository structure...",          4),
    ("inspecting_files",    "Inspecting relevant source files...",        5),
    ("analyzing_git",       "Analyzing recent git commits...",            4),
    ("correlating_evidence","Correlating evidence across findings...",    3),
    ("diagnosing",          "Formulating root-cause diagnosis...",        4),
    ("suggesting_fix",      "Generating suggested fix...",                3),
]


def _update_session(session_id: int, **fields):
    """Helper to update DebugSession fields in a fresh DB session."""
    with Session(engine) as db:
        investigation = db.get(DebugSession, session_id)
        if investigation:
            for key, value in fields.items():
                setattr(investigation, key, value)
            investigation.updated_at = datetime.utcnow()
            db.add(investigation)
            db.commit()


def _emit(session_id: int, event_type: str, message: str, step: str = None):
    """Emit an SSE event to the frontend."""
    data = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if step:
        data["step"] = step
    EventDispatcher.emit(session_id, event_type, data)


def run_investigation(session_id: int):
    """
    The main entry point called by FastAPI's BackgroundTasks.

    This function runs synchronously in a background thread. It:
    1. Registers the session with the AgentController
    2. Sets the session to 'running'
    3. Steps through each investigation phase
    4. Checks for cancellation / pause between steps
    5. On completion, sets status to 'completed'
    6. On error or cancellation, sets status to 'failed' or 'stopped'
    """
    AgentController.register_session(session_id)

    try:
        # Mark session as running
        _update_session(session_id, status="running", started_at=datetime.utcnow())
        _emit(session_id, "agent.status", "Agent started", step="initializing")

        for step_name, description, duration_secs in INVESTIGATION_STEPS:
            # --- Check cancellation ---
            if AgentController.is_cancelled(session_id):
                raise AgentCancelledException("Session was cancelled by user")

            # --- Check pause (blocks if paused) ---
            AgentController.wait_if_paused(session_id, timeout=0.5)
            if AgentController.is_cancelled(session_id):
                raise AgentCancelledException("Session was cancelled while paused")

            # --- Execute the step ---
            _update_session(session_id, current_step=step_name, current_action=description)
            _emit(session_id, "step.started", description, step=step_name)

            # Simulate work with interruptible sleep
            elapsed = 0.0
            while elapsed < duration_secs:
                if AgentController.is_cancelled(session_id):
                    raise AgentCancelledException("Session was cancelled during step")
                AgentController.wait_if_paused(session_id, timeout=0.5)
                time.sleep(0.5)
                elapsed += 0.5

            _emit(session_id, "step.completed", f"Completed: {description}", step=step_name)

        # --- All steps done ---
        _update_session(
            session_id,
            status="completed",
            current_step=None,
            current_action=None,
            completed_at=datetime.utcnow(),
        )
        _emit(session_id, "agent.status", "Investigation completed successfully")

    except AgentCancelledException:
        _update_session(
            session_id,
            status="stopped",
            current_step=None,
            current_action=None,
        )
        _emit(session_id, "agent.status", "Agent stopped by user")

    except Exception as e:
        _update_session(
            session_id,
            status="failed",
            current_step=None,
            current_action=None,
            error=str(e),
        )
        _emit(session_id, "agent.status", f"Agent failed: {e}")

    finally:
        AgentController.cleanup_session(session_id)
