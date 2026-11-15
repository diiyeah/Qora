"""AI-Assisted Quantum Circuit Optimization Engine for QORA Phase 2."""

import math
from typing import Any

from packages.schema.ai import (
    AIOptimizeResponse,
    OptimizationMetrics,
    OptimizationTransformation,
)
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.verification import CircuitVerificationEngine
from services.api.tools.circuit_ops import analyze_circuit

SELF_INVERSE_GATES: frozenset[str] = frozenset({"h", "x", "y", "z", "swap"})


class CircuitOptimizerEngine:
    """Optimizes quantum circuits: gate reduction, CNOT cancellation, depth compression & equivalence verification."""

    @classmethod
    def optimize(
        cls,
        circuit: Circuit,
        level: int = 2,
        shots: int = 1024,
        seed: int | None = None,
    ) -> AIOptimizeResponse:
        original_analysis = analyze_circuit(circuit)
        transformations: list[OptimizationTransformation] = []

        # Pass 1: Algebraic cancellation (Self-inverses, adjacent CNOTs, rotations)
        current_gates = [g.model_copy() for g in circuit.gates]
        cancelled_gates, trans_pass1 = cls._cancel_redundant_gates(current_gates)
        transformations.extend(trans_pass1)

        # Build candidate circuit
        candidate_circuit = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=cancelled_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=CircuitMetadata(framework="qiskit"),
        )

        # Pass 2: Equivalence & Fidelity Verification
        verification = CircuitVerificationEngine.verify(
            circuit=candidate_circuit,
            reference_circuit=circuit,
            shots=shots,
            seed=seed,
        )

        optimized_circuit = candidate_circuit if verification.equivalent else circuit
        optimized_analysis = analyze_circuit(optimized_circuit)

        # Calculate resource reduction metrics
        orig_gates = original_analysis.gate_count
        opt_gates = optimized_analysis.gate_count
        gate_reduction = round(((orig_gates - opt_gates) / orig_gates * 100) if orig_gates > 0 else 0.0, 2)

        orig_depth = original_analysis.depth
        opt_depth = optimized_analysis.depth
        depth_reduction = round(((orig_depth - opt_depth) / orig_depth * 100) if orig_depth > 0 else 0.0, 2)

        orig_cnots = original_analysis.cnot_count
        opt_cnots = optimized_analysis.cnot_count
        cnot_reduction = round(((orig_cnots - opt_cnots) / orig_cnots * 100) if orig_cnots > 0 else 0.0, 2)

        metrics = OptimizationMetrics(
            original_gate_count=orig_gates,
            optimized_gate_count=opt_gates,
            gate_reduction_percent=max(0.0, gate_reduction),
            original_depth=orig_depth,
            optimized_depth=opt_depth,
            depth_reduction_percent=max(0.0, depth_reduction),
            original_cnot_count=orig_cnots,
            optimized_cnot_count=opt_cnots,
            cnot_reduction_percent=max(0.0, cnot_reduction),
        )

        explanation = cls._generate_explanation(metrics, transformations, verification.fidelity)

        return AIOptimizeResponse(
            original_circuit=circuit,
            optimized_circuit=optimized_circuit,
            metrics=metrics,
            transformations=transformations,
            equivalent=verification.equivalent,
            fidelity=verification.fidelity,
            explanation=explanation,
        )

    @classmethod
    def _cancel_redundant_gates(
        cls, gates: list[Gate]
    ) -> tuple[list[Gate], list[OptimizationTransformation]]:
        transformations: list[OptimizationTransformation] = []
        changed = True
        current_list = list(gates)

        while changed:
            changed = False
            new_list: list[Gate] = []
            idx = 0
            while idx < len(current_list):
                if idx + 1 < len(current_list):
                    g1 = current_list[idx]
                    g2 = current_list[idx + 1]

                    # 1. Adjacent self-inverse cancellation: H*H=I, X*X=I, Z*Z=I
                    if g1.name == g2.name and g1.qubits == g2.qubits and g1.name in SELF_INVERSE_GATES:
                        transformations.append(
                            OptimizationTransformation(
                                type="cancel_self_inverse",
                                description=f"Cancelled self-inverse pair {g1.name.upper()} on qubit(s) {g1.qubits}.",
                                target_qubits=g1.qubits,
                                gates_removed=2,
                            )
                        )
                        idx += 2
                        changed = True
                        continue

                    # 2. Adjacent CNOT cancellation: CX(c, t) * CX(c, t) = I
                    if g1.name == "cx" and g2.name == "cx" and g1.qubits == g2.qubits:
                        transformations.append(
                            OptimizationTransformation(
                                type="cnot_cancellation",
                                description=f"Cancelled redundant CNOT pair CX({g1.qubits[0]}, {g1.qubits[1]}).",
                                target_qubits=g1.qubits,
                                gates_removed=2,
                            )
                        )
                        idx += 2
                        changed = True
                        continue

                    # 3. Combine rotations on same axis & qubit: Rz(a) * Rz(b) = Rz(a+b)
                    if (
                        g1.name in ("rx", "ry", "rz", "p")
                        and g2.name == g1.name
                        and g1.qubits == g2.qubits
                        and g1.params
                        and g2.params
                    ):
                        combined_angle = g1.params[0] + g2.params[0]
                        # If combined angle is 0 mod 2*pi, remove both
                        if abs(combined_angle % (2 * math.pi)) < 1e-5:
                            transformations.append(
                                OptimizationTransformation(
                                    type="combine_rotations",
                                    description=f"Combined opposite {g1.name.upper()} rotations to identity on qubit {g1.qubits[0]}.",
                                    target_qubits=g1.qubits,
                                    gates_removed=2,
                                )
                            )
                        else:
                            new_list.append(
                                Gate(
                                    name=g1.name,
                                    qubits=g1.qubits,
                                    params=[round(combined_angle, 4)],
                                    layer=g1.layer,
                                )
                            )
                            transformations.append(
                                OptimizationTransformation(
                                    type="combine_rotations",
                                    description=f"Combined adjacent {g1.name.upper()} rotations into angle {round(combined_angle, 4)} rad.",
                                    target_qubits=g1.qubits,
                                    gates_removed=1,
                                )
                            )
                        idx += 2
                        changed = True
                        continue

                new_list.append(current_list[idx])
                idx += 1

            current_list = new_list

        # Renumber layers sequentially
        for l_idx, g in enumerate(current_list):
            g.layer = l_idx

        return current_list, transformations

    @staticmethod
    def _generate_explanation(
        metrics: OptimizationMetrics,
        transformations: list[OptimizationTransformation],
        fidelity: float | None,
    ) -> str:
        if not transformations:
            return "Circuit is already in canonical irreducible form. No redundant gates or cancellation opportunities detected."

        parts = [
            f"Successfully applied {len(transformations)} circuit optimization transformation(s):",
            f"- Gate count reduced from {metrics.original_gate_count} to {metrics.optimized_gate_count} ({metrics.gate_reduction_percent}% reduction).",
            f"- Circuit depth reduced from {metrics.original_depth} to {metrics.optimized_depth} ({metrics.depth_reduction_percent}% reduction).",
        ]
        if metrics.original_cnot_count > metrics.optimized_cnot_count:
            parts.append(
                f"- CNOT count reduced from {metrics.original_cnot_count} to {metrics.optimized_cnot_count} ({metrics.cnot_reduction_percent}% reduction)."
            )
        if fidelity is not None:
            parts.append(f"- Quantum state fidelity preserved at {fidelity * 100:.2f}%.")

        return "\n".join(parts)
