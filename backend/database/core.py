import os
from sqlmodel import create_engine, Session

# We default to a local Postgres instance (as defined in docker-compose.yml)
# But we can override it with an environment variable for testing/production.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/autonomous_debugger"
)

# Create the SQLAlchemy Engine
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    """
    Dependency to yield a database session.
    Useful for FastAPI endpoints later.
    """
    with Session(engine) as session:
        yield session
