"""AI Copilot contracts for Phase 2: Execution-Grounded AI."""

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

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


def _normalize_circuit_dict(data: Any) -> Any:
    if isinstance(data, dict) and "circuit" in data and isinstance(data["circuit"], dict):
        c = dict(data["circuit"])
        if "metadata" not in c or c["metadata"] is None:
            c["metadata"] = {"framework": "qiskit", "task_id": None}
        if "num_qubits" not in c or c["num_qubits"] is None:
            c["num_qubits"] = 2
        if "num_clbits" not in c or c["num_clbits"] is None:
            c["num_clbits"] = 2
        if "gates" not in c or c["gates"] is None:
            c["gates"] = []
        elif isinstance(c["gates"], list):
            norm_gates = []
            for idx, g in enumerate(c["gates"]):
                if isinstance(g, dict):
                    g_copy = dict(g)
                    if "params" not in g_copy or g_copy["params"] is None:
                        g_copy["params"] = []
                    if "layer" not in g_copy or g_copy["layer"] is None:
                        g_copy["layer"] = idx
                    norm_gates.append(g_copy)
                else:
                    norm_gates.append(g)
            c["gates"] = norm_gates
        if "measurements" not in c or c["measurements"] is None:
            c["measurements"] = []
        data["circuit"] = c
    return data


class AIChatRequest(ContractModel):
    query: str
    circuit: Circuit | None = None
    source_code: str | None = None
    expected_behavior: str | None = None
    backend: Literal["aer"] = "aer"
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        return _normalize_circuit_dict(data)



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

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        return _normalize_circuit_dict(data)



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

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        return _normalize_circuit_dict(data)



class AIDiagnoseResponse(ContractModel):
    diagnosis: ErrorDiagnosis
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class AIGenerateRequest(ContractModel):
    prompt: str
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None


class AIGenerateResponse(ContractModel):
    circuit: Circuit
    explanation: str
    distribution: dict[str, float]
    statevector: dict[str, str] | None = None
    evidence: ExecutionEvidence
    validation_passed: bool = True
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


RepairActionType = Literal[
    "replace_gate",
    "insert_gate",
    "delete_gate",
    "swap_qubits",
    "modify_parameter",
    "add_measurement",
    "fix_clbit",
]


class RepairAction(ContractModel):
    action_type: RepairActionType
    gate_index: int | None = None
    original: dict[str, object] | None = None
    replacement: dict[str, object] | None = None
    explanation: str


class RepairProposal(ContractModel):
    original_circuit: Circuit
    repaired_circuit: Circuit
    error_category: ErrorCategory
    diagnosis_summary: str
    actions: list[RepairAction] = Field(default_factory=list)
    diff_summary: list[str] = Field(default_factory=list)
    code_diff: str = ""
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 0.95


class AIRepairRequest(ContractModel):
    circuit: Circuit
    source_code: str | None = None
    expected_behavior: str | None = None
    expected_distribution: dict[str, float] | None = None
    error_category: ErrorCategory | None = None
    iteration: Annotated[int, Field(ge=1, le=10, strict=True)] = 1

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        return _normalize_circuit_dict(data)



class AIRepairResponse(ContractModel):
    proposal: RepairProposal
    iteration: int = 1
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class CircuitVerificationRequest(ContractModel):
    circuit: Circuit
    reference_circuit: Circuit | None = None
    expected_behavior: str | None = None
    expected_distribution: dict[str, float] | None = None
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        res = _normalize_circuit_dict(data)
        if isinstance(res, dict) and "reference_circuit" in res and isinstance(res["reference_circuit"], dict):
            ref_wrapper = {"circuit": res["reference_circuit"]}
            norm_ref = _normalize_circuit_dict(ref_wrapper)
            res["reference_circuit"] = norm_ref["circuit"]
        return res


class CircuitVerificationResponse(ContractModel):
    validation_status: Literal["passed", "failed"] = "passed"
    execution_status: Literal["success", "error"] = "success"
    outcome: Literal["verified", "failed"] = "verified"
    fidelity: float | None = None
    tvd: float | None = None
    equivalent: bool = False
    expected_vs_observed: dict[str, dict[str, float]] = Field(default_factory=dict)
    evidence: ExecutionEvidence
    details: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class OptimizationMetrics(ContractModel):
    original_gate_count: int
    optimized_gate_count: int
    gate_reduction_percent: float
    original_depth: int
    optimized_depth: int
    depth_reduction_percent: float
    original_cnot_count: int
    optimized_cnot_count: int
    cnot_reduction_percent: float


class OptimizationTransformation(ContractModel):
    type: Literal[
        "cancel_self_inverse",
        "combine_rotations",
        "remove_identity",
        "cnot_cancellation",
        "transpiler_simplification",
    ]
    description: str
    target_qubits: list[int] = Field(default_factory=list)
    gates_removed: int = 0


class AIOptimizeRequest(ContractModel):
    circuit: Circuit
    level: Annotated[int, Field(ge=1, le=3, strict=True)] = 2
    shots: Annotated[int, Field(ge=1, le=100_000, strict=True)] = 1024
    seed: Annotated[int, Field(ge=0, le=2**32 - 1, strict=True)] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_circuit(cls, data: Any) -> Any:
        return _normalize_circuit_dict(data)


class AIOptimizeResponse(ContractModel):
    original_circuit: Circuit
    optimized_circuit: Circuit
    metrics: OptimizationMetrics
    transformations: list[OptimizationTransformation] = Field(default_factory=list)
    equivalent: bool = True
    fidelity: float | None = 1.0
    explanation: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)





