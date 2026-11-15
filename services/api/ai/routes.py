"""FastAPI route handlers for AI Copilot endpoints."""

from fastapi import APIRouter

from packages.schema.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIChatRequest,
    AIChatResponse,
    AIDiagnoseRequest,
    AIDiagnoseResponse,
    AIGenerateRequest,
    AIGenerateResponse,
    AIOptimizeRequest,
    AIOptimizeResponse,
    AIRepairRequest,
    AIRepairResponse,
)
from packages.schema.api import ErrorResponse
from services.api.ai.orchestrator import AIOrchestrator

router = APIRouter(
    tags=["ai-copilot"],
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)

_orchestrator = AIOrchestrator()


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(request: AIChatRequest) -> AIChatResponse:
    """Context-aware AI conversation grounded in actual circuit and execution data."""
    return _orchestrator.chat(request)


@router.post("/analyze", response_model=AIAnalyzeResponse)
def ai_analyze(request: AIAnalyzeRequest) -> AIAnalyzeResponse:
    """Circuit-grounded structural, behavioral, and simulation analysis."""
    return _orchestrator.analyze(request)


@router.post("/diagnose", response_model=AIDiagnoseResponse)
def ai_diagnose(request: AIDiagnoseRequest) -> AIDiagnoseResponse:
    """Detect and classify errors across 9 quantum programming error categories."""
    return _orchestrator.diagnose(request)


@router.post("/generate", response_model=AIGenerateResponse)
def ai_generate(request: AIGenerateRequest) -> AIGenerateResponse:
    """Generate, validate, and simulate quantum circuits from natural language instructions."""
    return _orchestrator.generate(request)


@router.post("/repair", response_model=AIRepairResponse)
def ai_repair(request: AIRepairRequest) -> AIRepairResponse:
    """Propose structured repairs, gate replacements, and code diffs for faulty circuits."""
    return _orchestrator.repair(request)


@router.post("/optimize", response_model=AIOptimizeResponse)
def ai_optimize(request: AIOptimizeRequest) -> AIOptimizeResponse:
    """Optimize quantum circuit via gate cancellation, rotation combining, and equivalence verification."""
    return _orchestrator.optimize(request)



