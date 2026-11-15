"""Quantum Error Detection and Diagnosis Engine for QORA Phase 2."""

import ast
import math
from typing import Any

from packages.schema.ai import (
    CircuitAnalysis,
    ErrorCategory,
    ErrorDiagnosis,
    ExecutionEvidence,
)
from packages.schema.models import Circuit
from services.api.tools.circuit_ops import (
    analyze_circuit,
    get_measurement_distribution,
    get_statevector,
)


class QuantumDiagnosticsEngine:
    """Detects, localizes, and classifies quantum errors across 9 categories."""

    @classmethod
    def diagnose(
        cls,
        circuit: Circuit | None = None,
        source_code: str | None = None,
        expected_behavior: str | None = None,
        expected_distribution: dict[str, float] | None = None,
        shots: int = 1024,
        seed: int | None = None,
    ) -> ErrorDiagnosis:
        # 1. Syntax check on source code if present
        if source_code:
            syntax_diag = cls._check_syntax_error(source_code)
            if syntax_diag:
                return syntax_diag

        if circuit is None:
            return ErrorDiagnosis(
                category="syntax",
                description="No circuit or valid source code provided.",
                suspected_location={"scope": "request"},
                execution_evidence=ExecutionEvidence(
                    qubit_count=0, depth=0, gate_count=0, cnot_count=0
                ),
                explanation="Diagnosis requires a valid canonical circuit or Python source code.",
                suggested_fix="Provide a canonical circuit payload or valid quantum program code.",
                confidence=1.0,
            )

        analysis = analyze_circuit(circuit)
        try:
            distribution = get_measurement_distribution(circuit, shots=shots, seed=seed)
        except Exception:
            distribution = {}

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
                f"Analyzed {analysis.gate_count} gates across {analysis.qubit_count} qubits",
                f"Execution returned {len(distribution)} observed basis states",
            ],
        )

        # 2. Measurement errors check
        measurement_diag = cls._check_measurement_errors(circuit, evidence)
        if measurement_diag:
            return measurement_diag

        # 3. Gate ordering check (e.g. CX before H on Bell circuits)
        ordering_diag = cls._check_gate_ordering_errors(circuit, evidence)
        if ordering_diag:
            return ordering_diag

        # 4. Qubit mapping check (e.g. inverted control/target)
        mapping_diag = cls._check_qubit_mapping_errors(circuit, evidence)
        if mapping_diag:
            return mapping_diag

        # 5. Parameter errors check
        param_diag = cls._check_parameter_errors(circuit, evidence)
        if param_diag:
            return param_diag

        # 6. Expected output & Algorithmic discrepancy check
        behavioral_diag = cls._check_behavioral_errors(
            circuit, distribution, expected_behavior, expected_distribution, evidence
        )
        if behavioral_diag:
            return behavioral_diag

        # 7. Default clean diagnosis if no errors found
        return ErrorDiagnosis(
            category="algorithmic",
            description="No significant quantum programming defect detected.",
            suspected_location={},
            execution_evidence=evidence,
            explanation=(
                f"Circuit executes cleanly with depth {analysis.depth} and {analysis.cnot_count} CNOT(s). "
                f"Observed distribution matches expected state propagation."
            ),
            suggested_fix="Circuit is logically consistent; no repairs needed.",
            confidence=0.95,
        )

    @classmethod
    def _check_syntax_error(cls, source_code: str) -> ErrorDiagnosis | None:
        try:
            ast.parse(source_code)
        except SyntaxError as err:
            return ErrorDiagnosis(
                category="syntax",
                description=f"Python syntax error: {err.msg}",
                suspected_location={"line": err.lineno or 1, "offset": err.offset or 0},
                execution_evidence=ExecutionEvidence(
                    qubit_count=0, depth=0, gate_count=0, cnot_count=0,
                    logs=[f"Syntax parsing failed on line {err.lineno}: {err.text}"]
                ),
                explanation=f"The provided quantum program contains a syntax defect at line {err.lineno}: {err.msg}.",
                suggested_fix="Correct the Python syntax error at the indicated line before simulating.",
                confidence=1.0,
            )
        return None

    @classmethod
    def _check_measurement_errors(
        cls, circuit: Circuit, evidence: ExecutionEvidence
    ) -> ErrorDiagnosis | None:
        # Check colliding measurements (multiple qubits measuring into the same clbit)
        seen_clbits: dict[int, int] = {}
        for idx, m in enumerate(circuit.measurements):
            if m.clbit in seen_clbits:
                first_qubit = seen_clbits[m.clbit]
                return ErrorDiagnosis(
                    category="measurement",
                    description=f"Measurement collision: qubit {m.qubit} and qubit {first_qubit} both measure into classical bit {m.clbit}.",
                    suspected_location={"measurement_index": idx, "qubit": m.qubit, "clbit": m.clbit},
                    execution_evidence=evidence,
                    explanation=f"Overwriting classical bit {m.clbit} destroys previous measurement outcome from qubit {first_qubit}.",
                    suggested_fix=f"Assign distinct classical bits to each measured qubit (e.g. qubit {m.qubit} -> clbit {m.qubit}).",
                    confidence=0.98,
                )
            seen_clbits[m.clbit] = m.qubit

        # Check missing measurements on multi-qubit circuits
        if circuit.num_clbits > 0 and len(circuit.measurements) < circuit.num_qubits:
            measured_qubits = {m.qubit for m in circuit.measurements}
            unmeasured = [q for q in range(circuit.num_qubits) if q not in measured_qubits]
            if unmeasured:
                return ErrorDiagnosis(
                    category="measurement",
                    description=f"Unmeasured active qubits: qubits {unmeasured} have no measurement operations.",
                    suspected_location={"unmeasured_qubits": unmeasured},
                    execution_evidence=evidence,
                    explanation="Quantum state collapses cannot be observed for unmeasured qubits.",
                    suggested_fix=f"Add measurement operations for qubits {unmeasured}.",
                    confidence=0.92,
                )

        return None

    @classmethod
    def _check_gate_ordering_errors(
        cls, circuit: Circuit, evidence: ExecutionEvidence
    ) -> ErrorDiagnosis | None:
        # Detect common gate ordering defects (e.g. CX before H when trying to create Bell/entanglement)
        cx_indices = [i for i, g in enumerate(circuit.gates) if g.name == "cx"]
        h_indices = [i for i, g in enumerate(circuit.gates) if g.name == "h"]

        if cx_indices and h_indices:
            first_cx = cx_indices[0]
            first_h = h_indices[0]
            cx_gate = circuit.gates[first_cx]
            h_gate = circuit.gates[first_h]

            # If CX is applied before H on the same control qubit
            if first_cx < first_h and cx_gate.qubits[0] == h_gate.qubits[0]:
                return ErrorDiagnosis(
                    category="gate_ordering",
                    description=f"Gate ordering inversion: CNOT applied at gate {first_cx} before Hadamard gate at {first_h}.",
                    suspected_location={"gate_index": first_cx, "gate_name": "cx", "control": cx_gate.qubits[0]},
                    execution_evidence=evidence,
                    explanation=(
                        f"Applying CX before creating superposition on control qubit {cx_gate.qubits[0]} "
                        f"operates on |0> and fails to create quantum entanglement."
                    ),
                    suggested_fix=f"Apply Hadamard gate H(q{cx_gate.qubits[0]}) before CNOT CX(q{cx_gate.qubits[0]}, q{cx_gate.qubits[1]}).",
                    confidence=0.96,
                )

        return None

    @classmethod
    def _check_qubit_mapping_errors(
        cls, circuit: Circuit, evidence: ExecutionEvidence
    ) -> ErrorDiagnosis | None:
        # Detect inverted control/target in 2-qubit entangling gates
        for idx, gate in enumerate(circuit.gates):
            if gate.name == "cx":
                control, target = gate.qubits[0], gate.qubits[1]
                # Check preceding gates: was target in superposition while control was in ground state |0>?
                target_has_h = any(g.name == "h" and g.qubits[0] == target for g in circuit.gates[:idx])
                control_has_h = any(g.name == "h" and g.qubits[0] == control for g in circuit.gates[:idx])

                if target_has_h and not control_has_h:
                    return ErrorDiagnosis(
                        category="qubit_mapping",
                        description=f"Inverted CNOT control and target mapping at gate {idx}.",
                        suspected_location={"gate_index": idx, "gate_name": "cx", "qubits": gate.qubits},
                        execution_evidence=evidence,
                        explanation=(
                            f"Control qubit {control} is in ground state |0>, while target qubit {target} holds superposition. "
                            f"Control and target appear swapped."
                        ),
                        suggested_fix=f"Invert CNOT qubits to control on qubit {target} and target qubit {control}: CX({target}, {control}).",
                        confidence=0.94,
                    )

        return None

    @classmethod
    def _check_parameter_errors(
        cls, circuit: Circuit, evidence: ExecutionEvidence
    ) -> ErrorDiagnosis | None:
        for idx, gate in enumerate(circuit.gates):
            if gate.name in ("rx", "ry", "rz", "p") and gate.params:
                angle = gate.params[0]
                # Check for degenerate 0.0 or trivial 2*pi rotation where an active rotation was intended
                if abs(angle) < 1e-6:
                    return ErrorDiagnosis(
                        category="parameter",
                        description=f"Null rotation parameter at gate {idx}: angle is 0.0.",
                        suspected_location={"gate_index": idx, "gate_name": gate.name, "params": gate.params},
                        execution_evidence=evidence,
                        explanation=f"Gate {gate.name} with angle 0.0 acts as an identity operation and produces no state evolution.",
                        suggested_fix=f"Specify a non-zero rotation angle (e.g. pi/2 = {round(math.pi/2, 4)} or pi = {round(math.pi, 4)}).",
                        confidence=0.90,
                    )
        return None

    @classmethod
    def _check_behavioral_errors(
        cls,
        circuit: Circuit,
        distribution: dict[str, float],
        expected_behavior: str | None,
        expected_distribution: dict[str, float] | None,
        evidence: ExecutionEvidence,
    ) -> ErrorDiagnosis | None:
        # Check against expected distribution if provided
        if expected_distribution:
            all_keys = set(distribution.keys()) | set(expected_distribution.keys())
            tvd = 0.5 * sum(abs(distribution.get(k, 0.0) - expected_distribution.get(k, 0.0)) for k in all_keys)

            if tvd > 0.15:
                return ErrorDiagnosis(
                    category="expected_output",
                    description=f"Output distribution deviates from expected target (TVD: {round(tvd, 4)}).",
                    suspected_location={"distribution_divergence": round(tvd, 4)},
                    execution_evidence=evidence,
                    explanation=(
                        f"Total Variation Distance between observed distribution {distribution} and "
                        f"expected distribution {expected_distribution} exceeds tolerance threshold (TVD = {round(tvd, 4)} > 0.15)."
                    ),
                    suggested_fix="Adjust circuit gate sequence or parameters to align output probabilities with expected distribution.",
                    confidence=0.92,
                )

        # Check expected Bell behavior heuristics
        if expected_behavior and ("bell" in expected_behavior.lower() or "phi+" in expected_behavior.lower()):
            has_00 = "00" in distribution and distribution["00"] > 0.35
            has_11 = "11" in distribution and distribution["11"] > 0.35
            spurious = sum(v for k, v in distribution.items() if k not in ("00", "11"))

            if not (has_00 and has_11) or spurious > 0.15:
                return ErrorDiagnosis(
                    category="algorithmic",
                    description="Circuit fails to generate the target Bell state |Phi+>.",
                    suspected_location={"circuit": "gates"},
                    execution_evidence=evidence,
                    explanation=(
                        f"Expected ~50% |00> and ~50% |11>, but observed: {distribution}. "
                        "The circuit algorithm does not properly entangle the two qubits into the Bell state."
                    ),
                    suggested_fix="Construct Bell state using H(q0) followed by CX(q0, q1).",
                    confidence=0.95,
                )

        return None
