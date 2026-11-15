"""Circuit Context Builder for grounding LLM prompts in quantum execution reality."""

from pydantic import BaseModel, Field

from packages.schema.ai import CircuitAnalysis, ExecutionEvidence
from packages.schema.models import Circuit
from services.api.tools.circuit_ops import (
    analyze_circuit,
    get_measurement_distribution,
    get_statevector,
)


class CircuitContext(BaseModel):
    query: str
    circuit: Circuit | None = None
    source_code: str | None = None
    expected_behavior: str | None = None
    backend: str = "aer"
    analysis: CircuitAnalysis | None = None
    distribution: dict[str, float] | None = None
    statevector: dict[str, str] | None = None
    evidence: ExecutionEvidence | None = None

    def to_system_prompt(self) -> str:
        return (
            "You are QORA AI Copilot, a senior quantum software engineer and assistant.\n"
            "CRITICAL PRINCIPLES:\n"
            "1. Ground all reasoning in the provided circuit structure and real backend execution results.\n"
            "2. Never hallucinate or invent quantum simulation results or statevectors.\n"
            "3. Cite verified execution evidence (gate counts, circuit depth, CNOT count, measurement distributions).\n"
            "4. Qubit 0 is the first wire and the leftmost bit in measurement bitstrings.\n"
            "5. Provide concise, direct, and actionable explanations."
        )

    def to_user_prompt(self) -> str:
        parts: list[str] = [f"User Query:\n{self.query}\n"]

        if self.circuit is not None:
            parts.append(
                f"Circuit Details:\n"
                f"- Qubits: {self.circuit.num_qubits}, Classical bits: {self.circuit.num_clbits}\n"
                f"- Gates count: {len(self.circuit.gates)}\n"
            )
            gate_list = ", ".join(
                f"{g.name}(q={g.qubits}" + (f", p={g.params}" if g.params else "") + ")"
                for g in self.circuit.gates
            )
            parts.append(f"- Gate sequence: {gate_list or 'None'}\n")

        if self.analysis is not None:
            parts.append(
                f"Circuit Analysis Metrics:\n"
                f"- Depth: {self.analysis.depth}\n"
                f"- CNOT count: {self.analysis.cnot_count}\n"
                f"- Multi-qubit gates: {self.analysis.multi_qubit_gates}\n"
                f"- Gate breakdown: {self.analysis.gate_breakdown}\n"
            )

        if self.distribution is not None:
            dist_str = ", ".join(f"|{k}⟩: {v * 100:.1f}%" for k, v in self.distribution.items())
            parts.append(f"Simulation Measurement Distribution ({self.backend}):\n{dist_str or 'None'}\n")

        if self.statevector is not None:
            sv_str = ", ".join(f"|{k}⟩: {v}" for k, v in self.statevector.items())
            parts.append(f"Statevector Amplitudes:\n{sv_str or 'None'}\n")

        if self.source_code:
            parts.append(f"Source Code:\n```python\n{self.source_code}\n```\n")

        if self.expected_behavior:
            parts.append(f"Expected Behavior:\n{self.expected_behavior}\n")

        return "\n".join(parts)


class CircuitContextBuilder:
    """Builds a rich, grounded execution context for AI reasoning."""

    @staticmethod
    def build_context(
        query: str,
        circuit: Circuit | None = None,
        source_code: str | None = None,
        expected_behavior: str | None = None,
        backend: str = "aer",
        simulate_if_present: bool = True,
        shots: int = 1024,
        seed: int | None = None,
    ) -> CircuitContext:
        analysis: CircuitAnalysis | None = None
        distribution: dict[str, float] | None = None
        statevector: dict[str, str] | None = None
        evidence: ExecutionEvidence | None = None

        if circuit is not None:
            analysis = analyze_circuit(circuit)

            if simulate_if_present:
                try:
                    distribution = get_measurement_distribution(circuit, shots=shots, seed=seed)
                except Exception:
                    distribution = None

                try:
                    statevector = get_statevector(circuit)
                except Exception:
                    statevector = None

            evidence = ExecutionEvidence(
                qubit_count=analysis.qubit_count,
                depth=analysis.depth,
                gate_count=analysis.gate_count,
                cnot_count=analysis.cnot_count,
                measurement_distribution=distribution or {},
                statevector_summary=statevector,
                logs=[
                    f"Analyzed circuit: {analysis.gate_count} gates, depth {analysis.depth}",
                    f"Simulated on backend '{backend}' with {shots} shots",
                ],
            )

        return CircuitContext(
            query=query,
            circuit=circuit,
            source_code=source_code,
            expected_behavior=expected_behavior,
            backend=backend,
            analysis=analysis,
            distribution=distribution,
            statevector=statevector,
            evidence=evidence,
        )
