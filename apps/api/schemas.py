from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RepositoryCreate(BaseModel):
    name: str
    url: str

class RepositoryResponse(BaseModel):
    id: int
    name: str
    url: str
    default_branch: str

class DebugSessionCreate(BaseModel):
    repository_id: int
    branch: Optional[str] = "main"
    bug_report: Optional[str] = ""

class DebugSessionResponse(BaseModel):
    id: int
    repository_id: int
    branch: str
    bug_report: str
    status: str
    current_step: Optional[str] = None
    current_action: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    final_patch_id: Optional[int] = None
class EvidenceResponse(BaseModel):
    id: int
    hypothesis_id: int
    type: str
    content: str
    is_supporting: bool

class PatchResponse(BaseModel):
    id: int
    hypothesis_id: int
    file_path: str
    original_snippet: str
    new_snippet: str
    status: str

class EventResponse(BaseModel):
    message: str
    timestamp: datetime
