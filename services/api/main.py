"""FastAPI application; run with uvicorn services.api.main:app."""

from typing import Literal

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Qora Quantum API",
    version="0.1.0",
    description="Phase 1 quantum backend. Week 1 foundation.",
)
router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Check API liveness; this does not probe simulator readiness."""
    return HealthResponse()


app.include_router(router, prefix="/v1")
app.include_router(router, include_in_schema=False)

