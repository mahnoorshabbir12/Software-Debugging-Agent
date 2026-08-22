from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Repository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    url: str
    default_branch: str = "main"

class Investigation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: Optional[int] = Field(default=None, foreign_key="repository.id")
    bug_report: str
    status: str = Field(default="pending") # pending, investigating, patching, resolved, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    final_patch_id: Optional[int] = None
    
    hypotheses: List["Hypothesis"] = Relationship(back_populates="investigation")

class Hypothesis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    investigation_id: int = Field(foreign_key="investigation.id")
    title: str
    description: str
    status: str = Field(default="untested") # untested, supported, refuted
    
    investigation: Investigation = Relationship(back_populates="hypotheses")
    evidence: List["Evidence"] = Relationship(back_populates="hypothesis")
    patches: List["Patch"] = Relationship(back_populates="hypothesis")

class Evidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hypothesis_id: int = Field(foreign_key="hypothesis.id")
    type: str # string, file, test_output
    content: str
    is_supporting: bool = True
    
    hypothesis: Hypothesis = Relationship(back_populates="evidence")

class Patch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hypothesis_id: int = Field(foreign_key="hypothesis.id")
    file_path: str
    original_snippet: str
    new_snippet: str
    status: str = Field(default="generated") # generated, valid, invalid
    
    hypothesis: Hypothesis = Relationship(back_populates="patches")
    test_runs: List["TestRun"] = Relationship(back_populates="patch")

class TestRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patch_id: int = Field(foreign_key="patch.id")
    passed: bool
    test_output: Optional[str] = None
    lint_output: Optional[str] = None
    type_output: Optional[str] = None
    
    patch: Patch = Relationship(back_populates="test_runs")

class ToolCall(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    investigation_id: int = Field(foreign_key="investigation.id")
    node: str # e.g. 'investigate', 'patch'
    tool_name: str
    args_json: str
    result_json: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
