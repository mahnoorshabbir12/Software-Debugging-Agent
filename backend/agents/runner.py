"""
Background runner for a debug session.

This module provides the function that FastAPI's BackgroundTasks will execute.
It steps through the investigation pipeline, updates the database, and emits
SSE events so the frontend timeline updates in real time.
"""

import time
import asyncio
import os
from datetime import datetime
from sqlmodel import Session

from backend.database.core import engine
from backend.database.models import DebugSession
from backend.agents.controller import AgentController, AgentCancelledException
from backend.agents.events import EventDispatcher
from backend.agents.supervisor import SupervisorGraph
from backend.llm import traced_config

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
    3. Executes the SupervisorGraph
    4. Checks for cancellation / pause between nodes
    5. On completion, sets status to 'completed'
    6. On error or cancellation, sets status to 'failed' or 'stopped'
    """
    AgentController.register_session(session_id)

    try:
        # Mark session as running
        _update_session(session_id, status="running", started_at=datetime.utcnow())
        _emit(session_id, "agent.status", "Agent started", step="initializing")
        _emit(session_id, "step.started", "Initializing debug session...", step="initializing")

        # Fetch bug report from db
        with Session(engine) as db:
            investigation = db.get(DebugSession, session_id)
            if not investigation:
                raise ValueError(f"Session {session_id} not found")
            bug_report = investigation.bug_report

        project_root = os.path.abspath(".")

        graph = SupervisorGraph()
        config = traced_config({"configurable": {"thread_id": str(session_id)}})
        _emit(session_id, "step.completed", "Completed: Initializing debug session...", step="initializing")

        # Execute the real agent graph
        for event in graph.app.stream({"bug_report": bug_report, "project_root": project_root}, config=config, stream_mode="updates"):
            # --- Check cancellation ---
            if AgentController.is_cancelled(session_id):
                raise AgentCancelledException("Session was cancelled by user")

            # --- Check pause (blocks if paused) ---
            AgentController.wait_if_paused(session_id, timeout=0.5)
            if AgentController.is_cancelled(session_id):
                raise AgentCancelledException("Session was cancelled while paused")
            
            # --- Emit node updates ---
            for node_name, node_state in event.items():
                description = f"Executed node: {node_name}"
                _update_session(session_id, current_step=node_name, current_action=description)
                _emit(session_id, "step.started", f"Running: {node_name}", step=node_name)
                _emit(session_id, "step.completed", description, step=node_name)

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

