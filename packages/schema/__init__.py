"""Shared Pydantic models and generated JSON Schema."""

from .models import Circuit, CircuitMetadata, Gate, Measurement
from .api import ErrorInfo, ErrorResponse, SimulationRequest, SimulationResult
from .ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIChatRequest,
    AIChatResponse,
    AIDiagnoseRequest,
    AIDiagnoseResponse,
    AIGenerateRequest,
    AIGenerateResponse,
    AIRepairRequest,
    AIRepairResponse,
    CircuitAnalysis,
    CircuitComparison,
    CircuitVerificationRequest,
    CircuitVerificationResponse,
    ErrorCategory,
    ErrorDiagnosis,
    ExecutionEvidence,
    RepairAction,
    RepairProposal,
    ToolCallRecord,
)

__all__ = [
    "Circuit", "CircuitMetadata", "Gate", "Measurement", "ErrorInfo",
    "ErrorResponse", "SimulationRequest", "SimulationResult",
    "AIChatRequest", "AIChatResponse", "AIAnalyzeRequest", "AIAnalyzeResponse",
    "AIDiagnoseRequest", "AIDiagnoseResponse", "AIGenerateRequest", "AIGenerateResponse",
    "AIRepairRequest", "AIRepairResponse", "RepairAction", "RepairProposal",
    "CircuitVerificationRequest", "CircuitVerificationResponse",
    "ErrorDiagnosis", "CircuitAnalysis", "CircuitComparison", "ErrorCategory",
    "ExecutionEvidence", "ToolCallRecord",
]
