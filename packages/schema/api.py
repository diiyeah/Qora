"""Week 1 HTTP contracts. Full circuit simulation arrives in Week 2."""

from typing import Annotated, Literal

from pydantic import Field

from .models import ContractModel

ErrorType = Literal[
    "syntax", "invalid_gate", "qubit_out_of_range", "measurement",
    "timeout", "sandbox_violation", "backend_unavailable",
]


class ErrorInfo(ContractModel):
    type: ErrorType
    line: int | None = None
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(ContractModel):
    error: ErrorInfo


class SimulationRequest(ContractModel):
    """Simulate the fixed two-qubit Bell circuit; circuit input is not accepted yet."""

    backend: Literal["aer"] = "aer"
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None


class BackendInfo(ContractModel):
    name: Literal["aer"] = "aer"
    version: str
    framework: Literal["qiskit"] = "qiskit"
    framework_version: str


class SimulationResult(ContractModel):
    circuit: Literal["bell"] = "bell"
    counts: dict[str, int]
    shots: int
    seed: int | None
    backend: BackendInfo
