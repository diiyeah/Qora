import pytest

from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.repair_engine import QuantumCircuitRepairEngine


def test_repair_gate_ordering_inversion() -> None:
    # CX before H
    faulty = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="cx", qubits=[0, 1], params=[], layer=0),
            Gate(name="h", qubits=[0], params=[], layer=1),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    proposal = QuantumCircuitRepairEngine.propose_repair(
        circuit=faulty,
        expected_behavior="Two-qubit Bell state",
    )

    assert proposal.error_category == "gate_ordering"
    assert len(proposal.actions) > 0
    assert proposal.repaired_circuit.gates[0].name == "h"
    assert proposal.repaired_circuit.gates[1].name == "cx"
    assert len(proposal.diff_summary) > 0
    assert "H(" in proposal.diff_summary[0] or "CX(" in proposal.diff_summary[0]
    assert proposal.code_diff


def test_repair_qubit_mapping_inversion() -> None:
    # Target qubit 1 has H, but CX controls on unexcited qubit 0
    faulty = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[1], params=[], layer=0),
            Gate(name="cx", qubits=[0, 1], params=[], layer=1),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    proposal = QuantumCircuitRepairEngine.propose_repair(circuit=faulty)

    assert proposal.error_category == "qubit_mapping"
    assert proposal.repaired_circuit.gates[1].qubits == [1, 0]
    assert any(a.action_type == "swap_qubits" for a in proposal.actions)


def test_repair_measurement_collision() -> None:
    # Both qubits measure into classical bit 0
    faulty = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="cx", qubits=[0, 1], params=[], layer=1),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=0),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    proposal = QuantumCircuitRepairEngine.propose_repair(circuit=faulty)

    assert proposal.error_category == "measurement"
    clbits = [m.clbit for m in proposal.repaired_circuit.measurements]
    assert len(set(clbits)) == 2  # No collisions
    assert any(a.action_type == "fix_clbit" for a in proposal.actions)


def test_repair_unmeasured_active_qubit() -> None:
    # 2 qubits but only 1 measurement
    faulty = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="cx", qubits=[0, 1], params=[], layer=1),
        ],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    proposal = QuantumCircuitRepairEngine.propose_repair(circuit=faulty)

    assert proposal.error_category == "measurement"
    assert len(proposal.repaired_circuit.measurements) == 2
    assert any(a.action_type == "add_measurement" for a in proposal.actions)


def test_repair_parameter_zero_angle() -> None:
    faulty = Circuit(
        num_qubits=1,
        num_clbits=1,
        gates=[Gate(name="rx", qubits=[0], params=[0.0], layer=0)],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    proposal = QuantumCircuitRepairEngine.propose_repair(circuit=faulty)

    assert proposal.error_category == "parameter"
    assert proposal.repaired_circuit.gates[0].params[0] > 0.0
    assert any(a.action_type == "modify_parameter" for a in proposal.actions)
