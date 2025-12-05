"""GhostLock backend entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import apikeys, auth, cases, entities, relationships
from app.schemas import HealthResponse

settings = get_settings()
app = FastAPI(title="GhostLock Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    """Simple health endpoint to confirm the API is running."""

    return HealthResponse(message="GhostLock Backend Running!")


app.include_router(auth.router)
app.include_router(apikeys.router)
app.include_router(cases.router)
app.include_router(entities.router)
app.include_router(relationships.router)
