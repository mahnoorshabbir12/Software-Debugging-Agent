from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class SubProjectMap(BaseModel):
    name: str = Field(description="Name of the sub-project or package (e.g. 'frontend', 'backend')")
    path: str = Field(description="Relative path to the sub-project directory")
    languages: List[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Detected frameworks (FastAPI, React, etc.)")
    dependencies_files: List[str] = Field(default_factory=list, description="Files defining dependencies")
    entry_points: List[str] = Field(default_factory=list, description="Detected entry points (main.py, index.js)")
    tests: List[str] = Field(default_factory=list, description="Detected test directories or files")

class RepositoryMap(BaseModel):
    root_path: str = Field(description="Absolute path to the repository root")
    is_monorepo: bool = Field(default=False, description="Whether this repository contains multiple sub-projects")
    languages: List[str] = Field(default_factory=list, description="Overall detected languages")
    frameworks: List[str] = Field(default_factory=list, description="Overall detected frameworks")
    sub_projects: List[SubProjectMap] = Field(default_factory=list, description="List of detected sub-projects")
    
    # Root level assets (for simple repos or monorepo roots)
    dependencies_files: List[str] = Field(default_factory=list, description="Root level dependency files")
    entry_points: List[str] = Field(default_factory=list, description="Root level entry points")
    tests: List[str] = Field(default_factory=list, description="Root level test directories/files")

class CodeChunk(BaseModel):
    file_path: str = Field(description="Relative path to the source file")
    symbol: Optional[str] = Field(default=None, description="Name of the function/class (if AST chunk)")
    chunk_type: str = Field(description="Type of chunk: 'text', 'function', 'class', etc.")
    language: str = Field(description="Programming language of the chunk")
    start_line: int = Field(description="1-indexed start line")
    end_line: int = Field(description="1-indexed end line")
    content: str = Field(description="The actual code content of the chunk")
    parent: Optional[str] = Field(default=None, description="The parent class/module if applicable")
