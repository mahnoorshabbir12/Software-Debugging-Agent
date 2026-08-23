from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from backend.database.core import get_session
from backend.database.models import Repository
from apps.api.schemas import RepositoryCreate, RepositoryResponse

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)

@router.post("/", response_model=RepositoryResponse, status_code=201)
def create_repository(
    repo_in: RepositoryCreate, 
    session: Session = Depends(get_session)
):
    """
    Register a new repository for the agent to monitor and investigate.
    """
    repo = Repository(name=repo_in.name, url=repo_in.url)
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo

@router.get("/", response_model=List[RepositoryResponse])
def get_repositories(session: Session = Depends(get_session)):
    """
    List all repositories.
    """
    repos = session.exec(select(Repository)).all()
    return repos
