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
