from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List

from backend.database.core import get_session
from backend.database.models import DebugSession, Evidence, Patch, Repository
from backend.agents.controller import AgentController
from backend.agents.events import EventDispatcher
from backend.agents.runner import run_investigation
from sse_starlette.sse import EventSourceResponse
from apps.api.schemas import (
    DebugSessionCreate,
    DebugSessionResponse,
    EvidenceResponse,
    PatchResponse,
    EventResponse
)

router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)

def _enrich_investigation(investigation: DebugSession, session: Session) -> dict:
    """Adds repository_name to a DebugSession for the API response."""
    data = investigation.model_dump() if hasattr(investigation, 'model_dump') else investigation.dict()
    repo = None
    if investigation.repository_id is not None:
        repo = session.get(Repository, investigation.repository_id)
    return data

@router.get("/", response_model=List[DebugSessionResponse])
def list_investigations(session: Session = Depends(get_session)):
    """
    List all debug sessions.
    """
    investigations = session.exec(select(DebugSession)).all()
    return [_enrich_investigation(inv, session) for inv in investigations]

@router.post("/", response_model=DebugSessionResponse, status_code=201)
def create_investigation(
    inv_in: DebugSessionCreate, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Trigger a new debug session for a bug report.
    """
    # Verify repo exists
    repo = session.get(Repository, inv_in.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    investigation = DebugSession(
        repository_id=inv_in.repository_id,
        branch=inv_in.branch,
        bug_report=inv_in.bug_report,
        status="starting"
    )
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    
    # Pre-register the SSE queue in the current event loop so that any events 
    # emitted immediately by the background task are buffered before the frontend connects.
    EventDispatcher.register_client(investigation.id)
    
    # Start the investigation pipeline in a background thread
    background_tasks.add_task(run_investigation, investigation.id)
    
    return _enrich_investigation(investigation, session)

@router.get("/{id}", response_model=DebugSessionResponse)
def get_investigation(id: int, session: Session = Depends(get_session)):
    """
    Get the status and details of an investigation.
    """
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return _enrich_investigation(investigation, session)

@router.get("/{id}/events")
def get_investigation_events(id: int):
    """
    SSE endpoint for streaming debug session events to the frontend.
    """
    queue = EventDispatcher.register_client(id)
    return EventSourceResponse(EventDispatcher.event_generator(id, queue))

@router.get("/{id}/evidence", response_model=List[EvidenceResponse])
def get_investigation_evidence(id: int, session: Session = Depends(get_session)):
    """
    Fetch the collected evidence for this investigation.
    """
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    # Gather evidence across all hypotheses for this investigation
    all_evidence = []
    for hypothesis in investigation.hypotheses:
        all_evidence.extend(hypothesis.evidence)
        
    return all_evidence

@router.get("/{id}/patch", response_model=List[PatchResponse])
def get_investigation_patches(id: int, session: Session = Depends(get_session)):
    """
    Fetch the generated patches for this investigation.
    """
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    all_patches = []
    for hypothesis in investigation.hypotheses:
        all_patches.extend(hypothesis.patches)
        
    return all_patches

@router.post("/{id}/validate")
def validate_investigation(id: int, session: Session = Depends(get_session)):
    """
    Trigger the validation loop (sandbox testing).
    Placeholder implementation that updates status.
    """
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    investigation.status = "validating"
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    
    return {"status": "validation_started", "investigation_id": id}

@router.post("/{id}/approve")
def approve_investigation(id: int, session: Session = Depends(get_session)):
    """
    Approve a patch for an investigation.
    Placeholder implementation that updates status.
    """
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    investigation.status = "resolved"
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    
    return {"status": "approved", "investigation_id": id}

@router.post("/{id}/stop", response_model=DebugSessionResponse)
def stop_investigation(id: int, session: Session = Depends(get_session)):
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    AgentController.request_cancellation(id)
    investigation.status = "stopping"
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    return _enrich_investigation(investigation, session)

@router.post("/{id}/pause", response_model=DebugSessionResponse)
def pause_investigation(id: int, session: Session = Depends(get_session)):
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    AgentController.request_pause(id)
    investigation.status = "paused"
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    return _enrich_investigation(investigation, session)

@router.post("/{id}/resume", response_model=DebugSessionResponse)
def resume_investigation(id: int, session: Session = Depends(get_session)):
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    AgentController.request_resume(id)
    investigation.status = "running"
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    return _enrich_investigation(investigation, session)

@router.post("/{id}/retry", response_model=DebugSessionResponse)
def retry_investigation(
    id: int, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    investigation = session.get(DebugSession, id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    # Pre-register the SSE queue to buffer events
    EventDispatcher.register_client(id)
        
    # Reset controller and status
    AgentController.register_session(id)
    investigation.status = "starting"
    investigation.error = None
    session.add(investigation)
    session.commit()
    session.refresh(investigation)
    
    # Restart the background investigation
    background_tasks.add_task(run_investigation, id)
    
    return _enrich_investigation(investigation, session)
