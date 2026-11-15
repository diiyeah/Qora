import pytest

from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.diagnostics import QuantumDiagnosticsEngine


def valid_bell_circuit() -> Circuit:
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


def test_diagnose_syntax_error() -> None:
    code = "def create_circuit(\n    qc = QuantumCircuit(2\n"
    diag = QuantumDiagnosticsEngine.diagnose(source_code=code)

    assert diag.category == "syntax"
    assert diag.confidence == 1.0
    assert "line" in diag.suspected_location
    assert diag.suggested_fix


def test_diagnose_measurement_collision() -> None:
    # Both qubits measured into clbit 0
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
    diag = QuantumDiagnosticsEngine.diagnose(circuit=faulty)

    assert diag.category == "measurement"
    assert diag.confidence >= 0.95
    assert diag.suspected_location.get("clbit") == 0


def test_diagnose_unmeasured_active_qubits() -> None:
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
    diag = QuantumDiagnosticsEngine.diagnose(circuit=faulty)

    assert diag.category == "measurement"
    unmeasured = diag.suspected_location.get("unmeasured_qubits")
    assert isinstance(unmeasured, list) and 1 in unmeasured


def test_diagnose_gate_ordering_cx_before_h() -> None:
    # CX before H on qubit 0
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
    diag = QuantumDiagnosticsEngine.diagnose(circuit=faulty)

    assert diag.category == "gate_ordering"
    assert diag.suspected_location.get("gate_name") == "cx"
    assert "before Hadamard" in diag.description


def test_diagnose_qubit_mapping_inverted_control() -> None:
    # Target qubit 1 has H, but CX controls on 0 (which is |0>) and targets 1
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
    diag = QuantumDiagnosticsEngine.diagnose(circuit=faulty)

    assert diag.category == "qubit_mapping"
    assert "Inverted CNOT" in diag.description
    assert diag.confidence >= 0.90


def test_diagnose_null_rotation_parameter() -> None:
    # rx with angle 0.0
    faulty = Circuit(
        num_qubits=1,
        num_clbits=1,
        gates=[
            Gate(name="rx", qubits=[0], params=[0.0], layer=0),
        ],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )
    diag = QuantumDiagnosticsEngine.diagnose(circuit=faulty)

    assert diag.category == "parameter"
    assert diag.suspected_location.get("gate_name") == "rx"


def test_diagnose_expected_distribution_mismatch() -> None:
    c = valid_bell_circuit()
    # Bell produces ~50% 00 and ~50% 11, so expected 100% 01 should trigger expected_output
    target_dist = {"01": 1.0}
    diag = QuantumDiagnosticsEngine.diagnose(
        circuit=c,
        expected_distribution=target_dist,
    )

    assert diag.category == "expected_output"
    assert "distribution_divergence" in diag.suspected_location


def test_diagnose_algorithmic_bell_failure() -> None:
    # Just an X gate on wire 0, no entanglement
    faulty = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="x", qubits=[0], params=[], layer=0),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )
    diag = QuantumDiagnosticsEngine.diagnose(
        circuit=faulty,
        expected_behavior="Prepare a two-qubit Bell state |Phi+>",
    )

    assert diag.category == "algorithmic"
    assert "Bell state" in diag.description


def test_diagnose_clean_bell_circuit() -> None:
    c = valid_bell_circuit()
    diag = QuantumDiagnosticsEngine.diagnose(
        circuit=c,
        expected_behavior="Bell state |Phi+>",
        expected_distribution={"00": 0.5, "11": 0.5},
    )

    assert "No significant quantum programming defect detected" in diag.description
    assert diag.execution_evidence.gate_count == 2
