import pytest
from fastapi.testclient import TestClient

from packages.schema.ai import CircuitVerificationResponse
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.verification import CircuitVerificationEngine
from services.api.main import app


def bell_circuit() -> Circuit:
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


def test_verify_bell_state_fidelity() -> None:
    c1 = bell_circuit()
    c2 = bell_circuit()

    res = CircuitVerificationEngine.verify(c1, reference_circuit=c2, shots=1024, seed=42)

    assert res.validation_status == "passed"
    assert res.execution_status == "success"
    assert res.outcome == "verified"
    assert res.equivalent is True
    assert res.fidelity is not None
    assert abs(res.fidelity - 1.0) < 0.01
    assert res.tvd is not None
    assert res.tvd < 0.05


def test_verify_distribution_matching() -> None:
    c = bell_circuit()
    res = CircuitVerificationEngine.verify(
        c,
        expected_distribution={"00": 0.5, "11": 0.5},
        shots=2048,
        seed=10,
    )

    assert res.outcome == "verified"
    assert res.equivalent is True
    assert res.tvd is not None
    assert res.tvd < 0.05


def test_verify_inequivalent_circuits() -> None:
    c_bell = bell_circuit()
    c_x = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[Gate(name="x", qubits=[0], params=[], layer=0)],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    res = CircuitVerificationEngine.verify(c_bell, reference_circuit=c_x, shots=1024, seed=42)

    assert res.outcome == "failed"
    assert res.equivalent is False
    assert res.fidelity is not None
    assert res.fidelity < 0.1


@pytest.mark.parametrize("path", ["/api/circuits/verify", "/v1/circuits/verify"])
def test_verify_api_endpoint(path: str) -> None:
    payload = {
        "circuit": bell_circuit().model_dump(mode="json"),
        "expected_distribution": {"00": 0.5, "11": 0.5},
    }
    with TestClient(app) as client:
        resp = client.post(path, json=payload)

    assert resp.status_code == 200
    data = CircuitVerificationResponse.model_validate(resp.json())
    assert data.outcome == "verified"
    assert data.validation_status == "passed"
