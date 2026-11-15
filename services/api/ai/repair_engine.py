"""Quantum Circuit Repair Proposal Engine for QORA Phase 2."""

import difflib
import math
from typing import Any

from packages.schema.ai import (
    ErrorDiagnosis,
    RepairAction,
    RepairProposal,
)
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.diagnostics import QuantumDiagnosticsEngine


class QuantumCircuitRepairEngine:
    """Generates structured repair proposals and before/after diffs for faulty circuits."""

    @classmethod
    def propose_repair(
        cls,
        circuit: Circuit,
        source_code: str | None = None,
        expected_behavior: str | None = None,
        expected_distribution: dict[str, float] | None = None,
        iteration: int = 1,
    ) -> RepairProposal:
        diagnosis = QuantumDiagnosticsEngine.diagnose(
            circuit=circuit,
            source_code=source_code,
            expected_behavior=expected_behavior,
            expected_distribution=expected_distribution,
        )

        repaired_circuit, actions, diff_summary = cls._generate_repair(
            circuit, diagnosis, expected_behavior
        )

        # Generate readable code diff
        orig_code = cls._circuit_to_pseudocode(circuit)
        repaired_code = cls._circuit_to_pseudocode(repaired_circuit)
        code_diff = "\n".join(
            difflib.unified_diff(
                orig_code.splitlines(),
                repaired_code.splitlines(),
                fromfile="original_circuit.py",
                tofile="repaired_circuit.py",
                lineterm="",
            )
        )

        return RepairProposal(
            original_circuit=circuit,
            repaired_circuit=repaired_circuit,
            error_category=diagnosis.category,
            diagnosis_summary=diagnosis.description,
            actions=actions,
            diff_summary=diff_summary,
            code_diff=code_diff or "# No code modifications required",
            confidence=diagnosis.confidence,
        )

    @classmethod
    def _generate_repair(
        cls,
        circuit: Circuit,
        diagnosis: ErrorDiagnosis,
        expected_behavior: str | None,
    ) -> tuple[Circuit, list[RepairAction], list[str]]:
        category = diagnosis.category
        actions: list[RepairAction] = []
        diff_summary: list[str] = []

        # Clone current gates and measurements
        gates = [g.model_copy() for g in circuit.gates]
        measurements = [m.model_copy() for m in circuit.measurements]
        num_qubits = circuit.num_qubits
        num_clbits = circuit.num_clbits

        # 1. GATE ORDERING REPAIR (e.g. CX before H)
        if category == "gate_ordering":
            cx_idx = None
            h_idx = None
            for idx, g in enumerate(gates):
                if g.name == "cx" and cx_idx is None:
                    cx_idx = idx
                elif g.name == "h" and h_idx is None:
                    h_idx = idx

            if cx_idx is not None and h_idx is not None and cx_idx < h_idx:
                # Reorder so H precedes CX
                h_gate = gates[h_idx]
                cx_gate = gates[cx_idx]

                gates[cx_idx] = Gate(
                    name=h_gate.name,
                    qubits=h_gate.qubits,
                    params=h_gate.params,
                    layer=cx_idx,
                )
                gates[h_idx] = Gate(
                    name=cx_gate.name,
                    qubits=cx_gate.qubits,
                    params=cx_gate.params,
                    layer=h_idx,
                )

                actions.append(
                    RepairAction(
                        action_type="replace_gate",
                        gate_index=cx_idx,
                        original=cx_gate.model_dump(mode="json"),
                        replacement=gates[cx_idx].model_dump(mode="json"),
                        explanation=f"Moved Hadamard H(q{h_gate.qubits[0]}) before CNOT CX(q{cx_gate.qubits[0]}, q{cx_gate.qubits[1]}).",
                    )
                )
                diff_summary.append(f"Gate {cx_idx}: Replaced CX({cx_gate.qubits}) with H({h_gate.qubits})")
                diff_summary.append(f"Gate {h_idx}: Replaced H({h_gate.qubits}) with CX({cx_gate.qubits})")

        # 2. QUBIT MAPPING REPAIR (e.g. inverted control/target)
        elif category == "qubit_mapping":
            loc_idx = diagnosis.suspected_location.get("gate_index")
            target_idx = int(loc_idx) if isinstance(loc_idx, (int, str)) else 0

            if 0 <= target_idx < len(gates) and gates[target_idx].name == "cx":
                old_gate = gates[target_idx]
                inverted_qubits = [old_gate.qubits[1], old_gate.qubits[0]]
                gates[target_idx] = Gate(
                    name="cx",
                    qubits=inverted_qubits,
                    params=[],
                    layer=old_gate.layer,
                )
                actions.append(
                    RepairAction(
                        action_type="swap_qubits",
                        gate_index=target_idx,
                        original=old_gate.model_dump(mode="json"),
                        replacement=gates[target_idx].model_dump(mode="json"),
                        explanation=f"Inverted CNOT control and target from {old_gate.qubits} to {inverted_qubits}.",
                    )
                )
                diff_summary.append(f"Gate {target_idx}: Inverted CX({old_gate.qubits}) -> CX({inverted_qubits})")

        # 3. MEASUREMENT REPAIRS
        elif category == "measurement":
            # Check collisions
            seen_clbits: set[int] = set()
            for idx, m in enumerate(measurements):
                if m.clbit in seen_clbits or m.clbit >= num_clbits:
                    # Fix to non-colliding bit
                    new_clbit = m.qubit
                    old_clbit = m.clbit
                    measurements[idx] = Measurement(qubit=m.qubit, clbit=new_clbit)
                    if new_clbit >= num_clbits:
                        num_clbits = new_clbit + 1

                    actions.append(
                        RepairAction(
                            action_type="fix_clbit",
                            gate_index=idx,
                            original={"qubit": m.qubit, "clbit": old_clbit},
                            replacement={"qubit": m.qubit, "clbit": new_clbit},
                            explanation=f"Reassigned measurement from colliding clbit {old_clbit} to clbit {new_clbit}.",
                        )
                    )
                    diff_summary.append(f"Measurement {idx}: Remapped clbit {old_clbit} -> {new_clbit}")
                seen_clbits.add(measurements[idx].clbit)

            # Check missing measurements
            measured_qubits = {m.qubit for m in measurements}
            for q in range(num_qubits):
                if q not in measured_qubits:
                    if q >= num_clbits:
                        num_clbits = q + 1
                    new_meas = Measurement(qubit=q, clbit=q)
                    measurements.append(new_meas)
                    actions.append(
                        RepairAction(
                            action_type="add_measurement",
                            gate_index=len(measurements) - 1,
                            original=None,
                            replacement={"qubit": q, "clbit": q},
                            explanation=f"Added missing measurement for active qubit {q} into clbit {q}.",
                        )
                    )
                    diff_summary.append(f"Added: Measure q{q} -> c{q}")

        # 4. PARAMETER REPAIRS
        elif category == "parameter":
            loc_idx = diagnosis.suspected_location.get("gate_index")
            target_idx = int(loc_idx) if isinstance(loc_idx, (int, str)) else 0
            if 0 <= target_idx < len(gates):
                old_gate = gates[target_idx]
                target_param = round(math.pi / 2, 4)
                gates[target_idx] = Gate(
                    name=old_gate.name,
                    qubits=old_gate.qubits,
                    params=[target_param],
                    layer=old_gate.layer,
                )
                actions.append(
                    RepairAction(
                        action_type="modify_parameter",
                        gate_index=target_idx,
                        original=old_gate.model_dump(mode="json"),
                        replacement=gates[target_idx].model_dump(mode="json"),
                        explanation=f"Adjusted parameter for gate {old_gate.name} from {old_gate.params} to [{target_param}].",
                    )
                )
                diff_summary.append(f"Gate {target_idx}: Set {old_gate.name} param to {target_param}")

        # 5. ALGORITHMIC / GENERAL DEFECT REPAIRS
        else:
            # If Bell state was requested but failed
            if expected_behavior and ("bell" in expected_behavior.lower() or "phi+" in expected_behavior.lower()):
                gates = [
                    Gate(name="h", qubits=[0], params=[], layer=0),
                    Gate(name="cx", qubits=[0, 1], params=[], layer=1),
                ]
                measurements = [
                    Measurement(qubit=0, clbit=0),
                    Measurement(qubit=1, clbit=1),
                ]
                num_qubits = 2
                num_clbits = 2
                actions.append(
                    RepairAction(
                        action_type="insert_gate",
                        explanation="Reconstructed canonical two-qubit Bell state algorithm: H(q0) -> CX(q0, q1).",
                    )
                )
                diff_summary.append("Rebuilt circuit with canonical Bell entangling gates: H(q0), CX(q0, q1)")

        repaired_circuit = Circuit(
            num_qubits=num_qubits,
            num_clbits=num_clbits,
            gates=gates,
            measurements=measurements,
            metadata=CircuitMetadata(framework="qiskit"),
        )

        return repaired_circuit, actions, diff_summary

    @staticmethod
    def _circuit_to_pseudocode(circuit: Circuit) -> str:
        lines = [
            f"# Quantum Circuit: {circuit.num_qubits} qubits, {circuit.num_clbits} clbits",
            f"qc = QuantumCircuit({circuit.num_qubits}, {circuit.num_clbits})",
        ]
        for g in circuit.gates:
            if g.params:
                lines.append(f"qc.{g.name}({g.params[0]}, *{g.qubits})")
            else:
                lines.append(f"qc.{g.name}(*{g.qubits})")
        for m in circuit.measurements:
            lines.append(f"qc.measure({m.qubit}, {m.clbit})")
        return "\n".join(lines)
