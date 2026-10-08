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
from packages.schema.models import Circuit
from services.api.analyze.metrics import analyze_circuit
from services.api.convert.qiskit import schema_to_qiskit

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


from services.api.simulate.base import BackendAdapter
from services.api.simulate.pennylane import PennyLaneAdapter

# Backend Registry
BACKENDS = {
    "aer": {
        "id": "aer",
        "name": "Aer Simulator",
        "max_qubits": 30,
        "supports_statevector": True,
        "supports_noise": True
    },
    "pennylane_default.qubit": {
        "id": "pennylane_default.qubit",
        "name": "PennyLane Default",
        "max_qubits": 20,
        "supports_statevector": True,
        "supports_noise": False
    },
    "cirq_simulator": {
        "id": "cirq_simulator",
        "name": "Cirq Simulator",
        "max_qubits": 20,
        "supports_statevector": True,
        "supports_noise": True
    },
    "qbraid_local": {
        "id": "qbraid_local",
        "name": "qBraid Local / Cloud",
        "max_qubits": 20,
        "supports_statevector": True,
        "supports_noise": True
    }
}

@router.get("/backends", tags=["backends"])
def list_backends():
    """List all registered backends and their capabilities (Week 7)."""
    return {"backends": list(BACKENDS.values())}

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


class AnalyzeRequest(BaseModel):
    circuit: Circuit

@router.post("/analyze", tags=["analysis"])
def analyze(request: AnalyzeRequest):
    """Analyze a circuit and return its metrics (Week 5)."""
    return analyze_circuit(request.circuit)


class ConvertRequest(BaseModel):
    circuit: Circuit | None = None
    code: str | None = None
    target_format: str

@router.post("/convert", tags=["conversion"])
def convert(request: ConvertRequest):
    """Convert between schema, QASM, and code representations (Week 4)."""
    if request.target_format == 'qasm':
        if not request.circuit:
            raise HTTPException(status_code=400, detail="circuit is required for QASM export")
        qc = schema_to_qiskit(request.circuit)
        # Using qasm2 for compatibility if qasm3 is not available
        try:
            from qiskit import qasm2
            qasm_str = qasm2.dumps(qc)
        except ImportError:
            qasm_str = qc.qasm()
        return {"converted": qasm_str}
    
    # Placeholder for other formats
    return {"converted": "Not implemented"}


app.include_router(router, prefix="/v1")
app.include_router(router, include_in_schema=False)

