"""FastAPI application; run with uvicorn services.api.main:app."""

from typing import Literal

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from packages.schema.api import ErrorInfo, ErrorResponse, SimulationRequest, SimulationResult
from services.api.errors import PlatformError
from services.api.simulate import simulate_bell

app = FastAPI(
    title="Qora Quantum API",
    version="0.1.0",
    description="Phase 1 quantum backend. Week 1 foundation.",
)
router = APIRouter()


@app.exception_handler(PlatformError)
async def platform_error_handler(request: Request, exc: PlatformError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    issues = exc.errors()
    backend_error = any("backend" in issue["loc"] for issue in issues)
    error = ErrorInfo(
        type="backend_unavailable" if backend_error else "syntax",
        message="Only the Aer backend is available in Week 1." if backend_error else "Invalid request.",
        details={"issues": [
            {"location": list(issue["loc"]), "message": issue["msg"], "type": issue["type"]}
            for issue in issues
        ]},
    )
    return JSONResponse(status_code=422, content=ErrorResponse(error=error).model_dump(mode="json"))


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error = ErrorInfo(type="syntax", message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=error).model_dump(mode="json"),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = ErrorInfo(type="backend_unavailable", message="The service could not complete this request.")
    return JSONResponse(status_code=500, content=ErrorResponse(error=error).model_dump(mode="json"))


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Check API liveness; this does not probe simulator readiness."""
    return HealthResponse()


@router.post(
    "/simulate", response_model=SimulationResult, tags=["simulation"],
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def simulate(request: SimulationRequest) -> SimulationResult:
    """Run the fixed Bell circuit on Aer. General circuit input arrives in Week 2."""
    return simulate_bell(shots=request.shots, seed=request.seed)


app.include_router(router, prefix="/v1")
app.include_router(router, include_in_schema=False)

