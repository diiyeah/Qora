import math
import pytest
from fastapi.testclient import TestClient

from packages.schema.ai import AIOptimizeResponse
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.optimizer import CircuitOptimizerEngine
from services.api.main import app


def test_optimize_self_inverse_cancellation() -> None:
    # Circuit with H-H on qubit 0 (should cancel to I)
    c = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="h", qubits=[0], params=[], layer=1),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    res = CircuitOptimizerEngine.optimize(c, level=2, shots=1024, seed=42)

    assert isinstance(res, AIOptimizeResponse)
    assert res.equivalent is True
    assert res.metrics.original_gate_count == 2
    assert res.metrics.optimized_gate_count == 0
    assert res.metrics.gate_reduction_percent == 100.0
    assert len(res.optimized_circuit.gates) == 0
    assert len(res.transformations) == 1
    assert res.transformations[0].type == "cancel_self_inverse"
    assert res.fidelity is not None
    assert abs(res.fidelity - 1.0) < 0.01


def test_optimize_cnot_cancellation() -> None:
    # Circuit with CX(0, 1) * CX(0, 1) = I
    c = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="cx", qubits=[0, 1], params=[], layer=1),
            Gate(name="cx", qubits=[0, 1], params=[], layer=2),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    res = CircuitOptimizerEngine.optimize(c, level=2, shots=1024, seed=42)

    assert res.equivalent is True
    assert res.metrics.original_cnot_count == 2
    assert res.metrics.optimized_cnot_count == 0
    assert res.metrics.cnot_reduction_percent == 100.0
    assert res.metrics.optimized_gate_count == 1
    assert res.optimized_circuit.gates[0].name == "h"
    assert len(res.transformations) == 1
    assert res.transformations[0].type == "cnot_cancellation"


def test_optimize_combine_rotations() -> None:
    # Adjacent Rz(0.3) + Rz(0.4) on qubit 0 -> Rz(0.7)
    c = Circuit(
        num_qubits=1,
        num_clbits=1,
        gates=[
            Gate(name="rz", qubits=[0], params=[0.3], layer=0),
            Gate(name="rz", qubits=[0], params=[0.4], layer=1),
        ],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    res = CircuitOptimizerEngine.optimize(c, level=2, shots=1024, seed=42)

    assert res.equivalent is True
    assert res.metrics.original_gate_count == 2
    assert res.metrics.optimized_gate_count == 1
    assert len(res.optimized_circuit.gates) == 1
    assert res.optimized_circuit.gates[0].name == "rz"
    assert res.optimized_circuit.gates[0].params == [0.7]


def test_optimize_opposite_rotations_cancel_to_identity() -> None:
    # Rx(pi/2) + Rx(-pi/2) -> 0 mod 2pi -> removed
    c = Circuit(
        num_qubits=1,
        num_clbits=1,
        gates=[
            Gate(name="rx", qubits=[0], params=[1.5708], layer=0),
            Gate(name="rx", qubits=[0], params=[-1.5708], layer=1),
        ],
        measurements=[Measurement(qubit=0, clbit=0)],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    res = CircuitOptimizerEngine.optimize(c, level=2, shots=1024, seed=42)

    assert res.equivalent is True
    assert res.metrics.optimized_gate_count == 0
    assert len(res.optimized_circuit.gates) == 0


def test_optimize_already_optimal_circuit() -> None:
    # Bell state is already irreducible
    c = Circuit(
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

    res = CircuitOptimizerEngine.optimize(c, level=2, shots=1024, seed=42)

    assert res.equivalent is True
    assert res.metrics.original_gate_count == 2
    assert res.metrics.optimized_gate_count == 2
    assert res.metrics.gate_reduction_percent == 0.0
    assert len(res.transformations) == 0
    assert "already in canonical irreducible form" in res.explanation


def test_optimize_api_endpoint() -> None:
    client = TestClient(app)
    c_dict = {
        "num_qubits": 2,
        "num_clbits": 2,
        "gates": [
            {"name": "x", "qubits": [1], "params": [], "layer": 0},
            {"name": "x", "qubits": [1], "params": [], "layer": 1},
        ],
        "measurements": [{"qubit": 1, "clbit": 1}],
        "metadata": {"framework": "qiskit"},
    }

    resp = client.post("/api/ai/optimize", json={"circuit": c_dict, "level": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["equivalent"] is True
    assert data["metrics"]["original_gate_count"] == 2
    assert data["metrics"]["optimized_gate_count"] == 0
    assert len(data["transformations"]) == 1
    assert data["transformations"][0]["type"] == "cancel_self_inverse"
