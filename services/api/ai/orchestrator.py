"""AI Orchestration Layer grounding LLM reasoning in deterministic quantum execution."""

from typing import Any

from packages.schema.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIChatRequest,
    AIChatResponse,
    AIDiagnoseRequest,
    AIDiagnoseResponse,
    AIGenerateRequest,
    AIGenerateResponse,
    CircuitAnalysis,
    ErrorDiagnosis,
    ExecutionEvidence,
    ToolCallRecord,
)
from packages.schema.models import Circuit
from services.api.ai.context_builder import CircuitContext, CircuitContextBuilder
from services.api.ai.diagnostics import QuantumDiagnosticsEngine
from services.api.ai.generator import NaturalLanguageCircuitGenerator
from services.api.ai.llm_client import LLMProvider, get_llm_provider
from services.api.tools.circuit_ops import (
    analyze_circuit,
    get_measurement_distribution,
    get_statevector,
)
from services.api.tools.registry import ToolRegistry, default_tool_registry


class AIOrchestrator:
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or default_tool_registry

    def chat(self, request: AIChatRequest) -> AIChatResponse:
        """Handle execution-grounded chat and reasoning over quantum circuits."""
        context = CircuitContextBuilder.build_context(
            query=request.query,
            circuit=request.circuit,
            source_code=request.source_code,
            expected_behavior=request.expected_behavior,
            backend=request.backend,
            simulate_if_present=True,
            shots=request.shots,
            seed=request.seed,
        )

        system_prompt = context.to_system_prompt()
        user_prompt = context.to_user_prompt()
        tool_schemas = self.tool_registry.get_definitions()

        llm_resp = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=tool_schemas,
        )

        tool_calls: list[ToolCallRecord] = []
        final_text = llm_resp.text

        # Execute any tools requested by the LLM
        for tc in llm_resp.tool_calls:
            result = self.tool_registry.execute(tc.name, tc.arguments)
            tool_calls.append(
                ToolCallRecord(tool=tc.name, args=tc.arguments, result=result)
            )

        evidence = context.evidence
        if not evidence and request.circuit is not None:
            # Fallback construct evidence if not created
            analysis = analyze_circuit(request.circuit)
            dist = get_measurement_distribution(request.circuit, shots=request.shots, seed=request.seed)
            evidence = ExecutionEvidence(
                qubit_count=analysis.qubit_count,
                depth=analysis.depth,
                gate_count=analysis.gate_count,
                cnot_count=analysis.cnot_count,
                measurement_distribution=dist,
            )

        return AIChatResponse(
            response=final_text,
            evidence=evidence,
            tool_calls=tool_calls,
        )

    def analyze(self, request: AIAnalyzeRequest) -> AIAnalyzeResponse:
        """Perform circuit-grounded structural and behavioral analysis."""
        circuit = request.circuit
        analysis = analyze_circuit(circuit)
        distribution = get_measurement_distribution(
            circuit, shots=request.shots, seed=request.seed
        )

        try:
            statevector = get_statevector(circuit)
        except Exception:
            statevector = None

        evidence = ExecutionEvidence(
            qubit_count=analysis.qubit_count,
            depth=analysis.depth,
            gate_count=analysis.gate_count,
            cnot_count=analysis.cnot_count,
            measurement_distribution=distribution,
            statevector_summary=statevector,
            logs=[
                f"Deterministic structural analysis: {analysis.gate_count} gates, depth {analysis.depth}",
                f"Aer simulation completed: {len(distribution)} observed basis states",
            ],
        )

        query = request.query or "Analyze this quantum circuit, its structure, and its simulation outcomes."
        context = CircuitContext(
            query=query,
            circuit=circuit,
            source_code=request.source_code,
            analysis=analysis,
            distribution=distribution,
            statevector=statevector,
            evidence=evidence,
        )

        system_prompt = context.to_system_prompt()
        user_prompt = context.to_user_prompt()

        llm_resp = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=self.tool_registry.get_definitions(),
        )

        return AIAnalyzeResponse(
            analysis=analysis,
            distribution=distribution,
            explanation=llm_resp.text,
            evidence=evidence,
            tool_calls=[
                ToolCallRecord(tool=tc.name, args=tc.arguments, result={})
                for tc in llm_resp.tool_calls
            ],
        )

    def diagnose(self, request: AIDiagnoseRequest) -> AIDiagnoseResponse:
        """Diagnose quantum program, structure, or simulation errors."""
        diagnosis = QuantumDiagnosticsEngine.diagnose(
            circuit=request.circuit,
            source_code=request.source_code,
            expected_behavior=request.expected_behavior,
            expected_distribution=request.expected_distribution,
            shots=request.shots,
            seed=request.seed,
        )

        return AIDiagnoseResponse(
            diagnosis=diagnosis,
            tool_calls=[
                ToolCallRecord(
                    tool="diagnose_error",
                    args={
                        "category": diagnosis.category,
                        "location": diagnosis.suspected_location,
                    },
                    result={"status": "completed", "confidence": diagnosis.confidence},
                )
            ],
        )

    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        """Synthesize, validate, and simulate quantum circuit from natural language."""
        generator = NaturalLanguageCircuitGenerator(llm_provider=self.llm_provider)
        return generator.generate(
            prompt=request.prompt,
            shots=request.shots,
            seed=request.seed,
        )


