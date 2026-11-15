"""AI Copilot contracts for Phase 2: Execution-Grounded AI."""

from typing import Annotated, Literal

from pydantic import Field

from .models import Circuit, ContractModel

ErrorCategory = Literal[
    "syntax",
    "invalid_gate",
    "qubit_mapping",
    "measurement",
    "gate_ordering",
    "parameter",
    "algorithmic",
    "expected_output",
    "conceptual_misconception",
]


class ToolCallRecord(ContractModel):
    tool: str
    args: dict[str, object] = Field(default_factory=dict)
    result: dict[str, object] = Field(default_factory=dict)


class ExecutionEvidence(ContractModel):
    qubit_count: int
    depth: int
    gate_count: int
    cnot_count: int
    measurement_distribution: dict[str, float] = Field(default_factory=dict)
    statevector_summary: dict[str, str] | None = None
    logs: list[str] = Field(default_factory=list)


class CircuitAnalysis(ContractModel):
    qubit_count: int
    clbit_count: int
    depth: int
    gate_count: int
    cnot_count: int
    multi_qubit_gates: int
    gate_breakdown: dict[str, int] = Field(default_factory=dict)


class CircuitComparison(ContractModel):
    equivalent: bool
    gate_count_diff: int
    depth_diff: int
    cnot_diff: int
    distribution_distance: float | None = None


class AIChatRequest(ContractModel):
    query: str
    circuit: Circuit | None = None
    source_code: str | None = None
    expected_behavior: str | None = None
    backend: Literal["aer"] = "aer"
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None


class AIChatResponse(ContractModel):
    response: str
    evidence: ExecutionEvidence | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class AIAnalyzeRequest(ContractModel):
    circuit: Circuit
    query: str | None = None
    source_code: str | None = None
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None


class AIAnalyzeResponse(ContractModel):
    analysis: CircuitAnalysis
    distribution: dict[str, float]
    explanation: str
    evidence: ExecutionEvidence
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ErrorDiagnosis(ContractModel):
    category: ErrorCategory
    description: str
    suspected_location: dict[str, object] = Field(default_factory=dict)
    execution_evidence: ExecutionEvidence
    explanation: str
    suggested_fix: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.95


class AIDiagnoseRequest(ContractModel):
    circuit: Circuit | None = None
    source_code: str | None = None
    expected_behavior: str | None = None
    expected_distribution: dict[str, float] | None = None
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None


class AIDiagnoseResponse(ContractModel):
    diagnosis: ErrorDiagnosis
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)

