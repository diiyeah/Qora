import pytest
from qiskit import QuantumCircuit

from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.convert import circuit_to_qiskit, qiskit_to_circuit


def sample_bell_circuit() -> Circuit:
    return Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="cx", qubits=[0, 1], params=[], layer=1),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )


def test_circuit_to_qiskit_bell() -> None:
    circuit = sample_bell_circuit()
    qc = circuit_to_qiskit(circuit)

    assert qc.num_qubits == 2
    assert qc.num_clbits == 2
    assert len(qc.data) == 4  # h, cx, measure, measure
    assert qc.data[0].operation.name == "h"
    assert qc.data[1].operation.name == "cx"


def test_qiskit_to_circuit_roundtrip() -> None:
    original = sample_bell_circuit()
    qc = circuit_to_qiskit(original)
    reconstructed = qiskit_to_circuit(qc)

    assert reconstructed.num_qubits == original.num_qubits
    assert reconstructed.num_clbits == original.num_clbits
    assert len(reconstructed.gates) == len(original.gates)
    assert reconstructed.gates[0].name == "h"
    assert reconstructed.gates[1].name == "cx"
    assert len(reconstructed.measurements) == 2


def test_parameterized_gates_conversion() -> None:
    circuit = Circuit(
        num_qubits=1,
        num_clbits=1,
        gates=[
            Gate(name="rx", qubits=[0], params=[1.5708], layer=0),
            Gate(name="ry", qubits=[0], params=[0.7854], layer=1),
            Gate(name="rz", qubits=[0], params=[3.1415], layer=2),
            Gate(name="p", qubits=[0], params=[0.5], layer=3),
        ],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )
    qc = circuit_to_qiskit(circuit)
    assert len(qc.data) == 5
    assert qc.data[0].operation.name == "rx"
    assert qc.data[1].operation.name == "ry"
    assert qc.data[2].operation.name == "rz"
    assert qc.data[3].operation.name == "p"


def test_multi_qubit_gates() -> None:
    circuit = Circuit(
        num_qubits=3,
        num_clbits=0,
        gates=[
            Gate(name="cz", qubits=[0, 1], params=[], layer=0),
            Gate(name="swap", qubits=[1, 2], params=[], layer=1),
            Gate(name="ccx", qubits=[0, 1, 2], params=[], layer=2),
        ],
        measurements=[],
        metadata=CircuitMetadata(framework="qiskit"),
    )
    qc = circuit_to_qiskit(circuit)
    assert qc.data[0].operation.name == "cz"
    assert qc.data[1].operation.name == "swap"
    assert qc.data[2].operation.name == "ccx"
