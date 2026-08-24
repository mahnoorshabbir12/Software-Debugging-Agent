from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.database.core import engine
from backend.observability import init_observability, get_logger
from apps.api.routers import repositories, investigations, observability

# Configure structured logging + register span sinks as early as possible so
# import-time and startup logs are captured and every span is persisted.
init_observability()
log = get_logger("api.server")

app = FastAPI(
    title="Autonomous Debugging Agent API",
    description="API for the autonomous software debugging agent.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Initialize the database tables on startup if they don't exist
# In a real production scenario, we'd rely on Alembic migrations.
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    log.info("api.startup", message="Database tables ensured; API ready")

app.include_router(repositories.router)
app.include_router(investigations.router)
app.include_router(observability.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Autonomous Debugging Agent API"}
