"""Quantum Circuit Verification Engine for QORA Phase 2."""

from typing import Any, Literal

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from packages.schema.ai import (
    CircuitVerificationResponse,
    ExecutionEvidence,
)
from packages.schema.models import Circuit
from services.api.convert import circuit_to_qiskit
from services.api.tools.circuit_ops import (
    analyze_circuit,
    get_measurement_distribution,
    get_statevector,
    simulate_circuit,
)


class CircuitVerificationEngine:
    """Rigorous quantum verification: schema, simulation, distribution TVD, and state fidelity."""

    @classmethod
    def verify(
        cls,
        circuit: Circuit,
        reference_circuit: Circuit | None = None,
        expected_behavior: str | None = None,
        expected_distribution: dict[str, float] | None = None,
        shots: int = 1024,
        seed: int | None = None,
    ) -> CircuitVerificationResponse:
        details: list[str] = []

        # 1. Schema Validation
        validation_status: Literal["passed", "failed"] = "passed"
        execution_status: Literal["success", "error"] = "success"
        try:
            Circuit.model_validate(circuit.model_dump(mode="json"))
            validation_status = "passed"
            details.append("Schema contract validation passed.")
        except Exception as exc:
            return CircuitVerificationResponse(
                validation_status="failed",
                execution_status="error",
                outcome="failed",
                details=[f"Schema validation error: {exc}"],
                evidence=ExecutionEvidence(qubit_count=0, depth=0, gate_count=0, cnot_count=0),
            )

        # 2. Execution & Metrics
        try:
            analysis = analyze_circuit(circuit)
            dist = get_measurement_distribution(circuit, shots=shots, seed=seed)
            execution_status = "success"
            details.append(f"Simulation completed: {analysis.gate_count} gates, depth {analysis.depth}.")
        except Exception as exc:
            return CircuitVerificationResponse(
                validation_status="passed",
                execution_status="error",
                outcome="failed",
                details=[f"Execution simulation failed: {exc}"],
                evidence=ExecutionEvidence(qubit_count=0, depth=0, gate_count=0, cnot_count=0),
            )

        try:
            statevector_summary = get_statevector(circuit)
        except Exception:
            statevector_summary = None

        evidence = ExecutionEvidence(
            qubit_count=analysis.qubit_count,
            depth=analysis.depth,
            gate_count=analysis.gate_count,
            cnot_count=analysis.cnot_count,
            measurement_distribution=dist,
            statevector_summary=statevector_summary,
            logs=details,
        )

        expected_vs_observed: dict[str, dict[str, float]] = {
            "observed": dist,
            "expected": expected_distribution or {},
        }

        fidelity_score: float | None = None
        tvd_score: float | None = None
        equivalent = False
        outcome = "verified"

        # 3. Verification against Reference Circuit (Statevector Fidelity & Equivalence)
        if reference_circuit is not None:
            try:
                qc_candidate = cls._strip_measurements(circuit)
                qc_ref = cls._strip_measurements(reference_circuit)

                sv_cand = Statevector.from_instruction(qc_candidate)
                sv_ref = Statevector.from_instruction(qc_ref)

                fid = float(state_fidelity(sv_cand, sv_ref))
                fidelity_score = round(fid, 4)

                ref_dist = get_measurement_distribution(reference_circuit, shots=shots, seed=seed)
                expected_vs_observed["expected"] = ref_dist

                all_keys = set(dist.keys()) | set(ref_dist.keys())
                tvd = 0.5 * sum(abs(dist.get(k, 0.0) - ref_dist.get(k, 0.0)) for k in all_keys)
                tvd_score = round(tvd, 4)

                if fidelity_score >= 0.95 and tvd <= 0.08:
                    equivalent = True
                    details.append(f"State fidelity {fidelity_score} and TVD {tvd_score} meet equivalence threshold.")
                else:
                    equivalent = False
                    outcome = "failed"
                    details.append(f"Equivalence check failed: Fidelity {fidelity_score} (< 0.95) or TVD {tvd_score} (> 0.08).")
            except Exception as exc:
                outcome = "failed"
                details.append(f"State fidelity calculation failed: {exc}")

        # 4. Verification against Expected Distribution
        elif expected_distribution:
            all_keys = set(dist.keys()) | set(expected_distribution.keys())
            tvd = 0.5 * sum(abs(dist.get(k, 0.0) - expected_distribution.get(k, 0.0)) for k in all_keys)
            tvd_score = round(tvd, 4)

            if tvd <= 0.08:
                equivalent = True
                details.append(f"TVD {tvd_score} meets target distribution tolerance (<= 0.08).")
            else:
                equivalent = False
                outcome = "failed"
                details.append(f"TVD {tvd_score} exceeds target distribution tolerance (> 0.08).")

        # 5. Verification against Expected Behavior string (e.g. Bell state)
        elif expected_behavior and ("bell" in expected_behavior.lower() or "phi+" in expected_behavior.lower()):
            p00 = dist.get("00", 0.0)
            p11 = dist.get("11", 0.0)
            if abs(p00 - 0.5) <= 0.12 and abs(p11 - 0.5) <= 0.12:
                details.append(f"Observed Bell state probabilities (|00>: {p00:.2f}, |11>: {p11:.2f}) verified.")
                equivalent = True
            else:
                outcome = "failed"
                details.append(f"Observed distribution {dist} does not satisfy Bell state criteria.")

        return CircuitVerificationResponse(
            validation_status=validation_status,
            execution_status=execution_status,
            outcome=outcome,  # type: ignore[arg-type]
            fidelity=fidelity_score,
            tvd=tvd_score,
            equivalent=equivalent,
            expected_vs_observed=expected_vs_observed,
            evidence=evidence,
            details=details,
        )

    @staticmethod
    def _strip_measurements(circuit: Circuit) -> QuantumCircuit:
        qc = QuantumCircuit(circuit.num_qubits)
        for g in circuit.gates:
            name = g.name
            q = g.qubits
            p = g.params
            if name == "h":
                qc.h(q[0])
            elif name == "x":
                qc.x(q[0])
            elif name == "y":
                qc.y(q[0])
            elif name == "z":
                qc.z(q[0])
            elif name == "s":
                qc.s(q[0])
            elif name == "sdg":
                qc.sdg(q[0])
            elif name == "t":
                qc.t(q[0])
            elif name == "tdg":
                qc.tdg(q[0])
            elif name == "rx":
                qc.rx(p[0], q[0])
            elif name == "ry":
                qc.ry(p[0], q[0])
            elif name == "rz":
                qc.rz(p[0], q[0])
            elif name == "p":
                qc.p(p[0], q[0])
            elif name == "cx":
                qc.cx(q[0], q[1])
            elif name == "cz":
                qc.cz(q[0], q[1])
            elif name == "swap":
                qc.swap(q[0], q[1])
            elif name == "ccx":
                qc.ccx(q[0], q[1], q[2])
        return qc
