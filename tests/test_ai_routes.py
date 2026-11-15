from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.schema.ai import (
    AIAnalyzeResponse,
    AIChatResponse,
    AIDiagnoseResponse,
    AIGenerateResponse,
    AIRepairResponse,
)
from services.api.main import app


def sample_bell_payload() -> dict[str, Any]:
    return {
        "num_qubits": 2,
        "num_clbits": 2,
        "gates": [
            {"name": "h", "qubits": [0], "params": [], "layer": 0},
            {"name": "cx", "qubits": [0, 1], "params": [], "layer": 1},
        ],
        "measurements": [
            {"qubit": 0, "clbit": 0},
            {"qubit": 1, "clbit": 1},
        ],
        "metadata": {"framework": "qiskit", "task_id": None},
    }


@pytest.mark.parametrize("prefix", ["/api/ai", "/v1/ai"])
def test_ai_chat_endpoint(prefix: str) -> None:
    with TestClient(app) as client:
        resp = client.post(
            f"{prefix}/chat",
            json={
                "query": "What is this circuit doing?",
                "circuit": sample_bell_payload(),
                "shots": 512,
            },
        )
    assert resp.status_code == 200
    data = AIChatResponse.model_validate(resp.json())
    assert data.response
    assert data.evidence is not None
    assert data.evidence.gate_count == 2
    assert "00" in data.evidence.measurement_distribution


@pytest.mark.parametrize("prefix", ["/api/ai", "/v1/ai"])
def test_ai_analyze_endpoint(prefix: str) -> None:
    with TestClient(app) as client:
        resp = client.post(
            f"{prefix}/analyze",
            json={
                "circuit": sample_bell_payload(),
                "shots": 512,
                "seed": 42,
            },
        )
    assert resp.status_code == 200
    data = AIAnalyzeResponse.model_validate(resp.json())
    assert data.analysis.gate_count == 2
    assert data.analysis.cnot_count == 1
    assert "00" in data.distribution
    assert data.explanation


def test_ai_analyze_validation_error() -> None:
    with TestClient(app) as client:
        # Invalid circuit: negative shots
        resp = client.post(
            "/api/ai/analyze",
            json={
                "circuit": sample_bell_payload(),
                "shots": -5,
            },
        )
    assert resp.status_code == 422
    assert "error" in resp.json()


@pytest.mark.parametrize("prefix", ["/api/ai", "/v1/ai"])
def test_ai_diagnose_endpoint(prefix: str) -> None:
    faulty_payload = {
        "num_qubits": 2,
        "num_clbits": 2,
        "gates": [
            {"name": "cx", "qubits": [0, 1], "params": [], "layer": 0},
            {"name": "h", "qubits": [0], "params": [], "layer": 1},
        ],
        "measurements": [
            {"qubit": 0, "clbit": 0},
            {"qubit": 1, "clbit": 1},
        ],
        "metadata": {"framework": "qiskit"},
    }
    with TestClient(app) as client:
        resp = client.post(
            f"{prefix}/diagnose",
            json={
                "circuit": faulty_payload,
                "expected_behavior": "Two-qubit Bell state",
            },
        )
    assert resp.status_code == 200
    data = AIDiagnoseResponse.model_validate(resp.json())
    assert data.diagnosis.category == "gate_ordering"
    assert data.diagnosis.confidence > 0.9
    assert data.diagnosis.suggested_fix


@pytest.mark.parametrize("prefix", ["/api/ai", "/v1/ai"])
def test_ai_generate_endpoint(prefix: str) -> None:
    with TestClient(app) as client:
        resp = client.post(
            f"{prefix}/generate",
            json={
                "prompt": "Create a two-qubit Bell state",
                "shots": 1024,
                "seed": 42,
            },
        )
    assert resp.status_code == 200
    data = AIGenerateResponse.model_validate(resp.json())
    assert data.circuit.num_qubits == 2
    assert len(data.circuit.gates) == 2
    assert data.validation_passed is True
    assert "00" in data.distribution
    assert "11" in data.distribution


@pytest.mark.parametrize("prefix", ["/api/ai", "/v1/ai"])
def test_ai_repair_endpoint(prefix: str) -> None:
    faulty_payload = {
        "num_qubits": 2,
        "num_clbits": 2,
        "gates": [
            {"name": "cx", "qubits": [0, 1], "params": [], "layer": 0},
            {"name": "h", "qubits": [0], "params": [], "layer": 1},
        ],
        "measurements": [
            {"qubit": 0, "clbit": 0},
            {"qubit": 1, "clbit": 1},
        ],
        "metadata": {"framework": "qiskit"},
    }
    with TestClient(app) as client:
        resp = client.post(
            f"{prefix}/repair",
            json={
                "circuit": faulty_payload,
                "expected_behavior": "Two-qubit Bell state",
                "iteration": 1,
            },
        )
    assert resp.status_code == 200
    data = AIRepairResponse.model_validate(resp.json())
    assert data.proposal.error_category == "gate_ordering"
    assert len(data.proposal.actions) > 0
    assert data.proposal.repaired_circuit.gates[0].name == "h"
    assert data.proposal.repaired_circuit.gates[1].name == "cx"
    assert data.proposal.code_diff



