"""End-to-End integration test covering the complete Phase 2 Quantum Copilot lifecycle."""

import time
import pytest
from fastapi.testclient import TestClient

from packages.schema.ai import (
    AIChatResponse,
    AIDiagnoseResponse,
    AIGenerateResponse,
    AIOptimizeResponse,
    AIRepairResponse,
    CircuitVerificationResponse,
)
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_e2e_full_quantum_copilot_lifecycle(client: TestClient) -> None:
    """Complete lifecycle: NL Generation -> Fault Injection -> Diagnosis -> Repair -> Verification -> Optimization -> Grounded Chat."""

    # -------------------------------------------------------------
    # Step 1: Natural Language Generation
    # -------------------------------------------------------------
    gen_resp = client.post(
        "/api/ai/generate",
        json={"prompt": "Create a two-qubit Bell state |Φ+⟩", "shots": 1024, "seed": 42},
    )
    assert gen_resp.status_code == 200
    gen_data = AIGenerateResponse.model_validate(gen_resp.json())
    assert gen_data.circuit.num_qubits == 2
    assert len(gen_data.circuit.gates) == 2
    assert gen_data.circuit.gates[0].name == "h"
    assert gen_data.circuit.gates[1].name == "cx"
    assert "00" in gen_data.distribution
    assert "11" in gen_data.distribution
    assert gen_data.validation_passed is True

    original_circuit = gen_data.circuit

    # -------------------------------------------------------------
    # Step 2: Fault Injection (Gate Ordering Inversion: CX before H)
    # -------------------------------------------------------------
    faulty_circuit = Circuit(
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

    # -------------------------------------------------------------
    # Step 3: Circuit-Grounded Diagnosis
    # -------------------------------------------------------------
    diag_resp = client.post(
        "/api/ai/diagnose",
        json={
            "circuit": faulty_circuit.model_dump(mode="json"),
            "expected_behavior": "Two-qubit Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2",
            "expected_distribution": {"00": 0.5, "11": 0.5},
        },
    )
    assert diag_resp.status_code == 200
    diag_data = AIDiagnoseResponse.model_validate(diag_resp.json())
    assert diag_data.diagnosis.category in ("gate_ordering", "expected_output", "algorithmic")
    assert diag_data.diagnosis.suspected_location is not None
    assert diag_data.diagnosis.explanation
    assert diag_data.diagnosis.confidence >= 0.85

    # -------------------------------------------------------------
    # Step 4: Execution-Guided Repair Proposal
    # -------------------------------------------------------------
    repair_resp = client.post(
        "/api/ai/repair",
        json={
            "circuit": faulty_circuit.model_dump(mode="json"),
            "expected_behavior": "Two-qubit Bell state |Φ+⟩",
            "expected_distribution": {"00": 0.5, "11": 0.5},
            "iteration": 1,
        },
    )
    assert repair_resp.status_code == 200
    repair_data = AIRepairResponse.model_validate(repair_resp.json())
    repaired_circuit = repair_data.proposal.repaired_circuit
    assert len(repair_data.proposal.actions) > 0
    assert repair_data.proposal.code_diff
    # Repaired circuit should have H before CX
    assert repaired_circuit.gates[0].name == "h"
    assert repaired_circuit.gates[1].name == "cx"

    # -------------------------------------------------------------
    # Step 5: Verification of Repaired Circuit
    # -------------------------------------------------------------
    verify_resp = client.post(
        "/api/circuits/verify",
        json={
            "circuit": repaired_circuit.model_dump(mode="json"),
            "reference_circuit": original_circuit.model_dump(mode="json"),
            "expected_behavior": "Two-qubit Bell state |Φ+⟩",
            "shots": 1024,
            "seed": 42,
        },
    )
    assert verify_resp.status_code == 200
    verify_data = CircuitVerificationResponse.model_validate(verify_resp.json())
    assert verify_data.outcome == "verified"
    assert verify_data.equivalent is True
    assert verify_data.fidelity is not None
    assert abs(verify_data.fidelity - 1.0) < 0.05

    # -------------------------------------------------------------
    # Step 6: Circuit Optimization (Adding Cancellable Redundancies)
    # -------------------------------------------------------------
    redundant_circuit = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="h", qubits=[0], params=[], layer=0),
            Gate(name="x", qubits=[1], params=[], layer=1),
            Gate(name="x", qubits=[1], params=[], layer=2),  # X*X = I
            Gate(name="cx", qubits=[0, 1], params=[], layer=3),
            Gate(name="cx", qubits=[0, 1], params=[], layer=4),
            Gate(name="cx", qubits=[0, 1], params=[], layer=5),  # CX*CX = I
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )

    opt_resp = client.post(
        "/api/ai/optimize",
        json={"circuit": redundant_circuit.model_dump(mode="json"), "level": 2},
    )
    assert opt_resp.status_code == 200
    opt_data = AIOptimizeResponse.model_validate(opt_resp.json())
    assert opt_data.equivalent is True
    assert opt_data.metrics.original_gate_count == 6
    assert opt_data.metrics.optimized_gate_count == 2
    assert opt_data.metrics.gate_reduction_percent > 60.0
    assert len(opt_data.transformations) >= 2

    # -------------------------------------------------------------
    # Step 7: Grounded Chat Conversation & Reasoning
    # -------------------------------------------------------------
    chat_resp = client.post(
        "/api/ai/chat",
        json={
            "query": "Explain what this circuit does and provide its measurement statistics.",
            "circuit": opt_data.optimized_circuit.model_dump(mode="json"),
            "shots": 512,
            "seed": 42,
        },
    )
    assert chat_resp.status_code == 200
    chat_data = AIChatResponse.model_validate(chat_resp.json())
    assert chat_data.response
    assert chat_data.evidence is not None
    assert chat_data.evidence.qubit_count == 2
    assert "00" in chat_data.evidence.measurement_distribution


def test_e2e_copilot_latency_sla(client: TestClient) -> None:
    """Verify performance SLAs for key AI Copilot endpoints."""
    bell_circuit = Circuit(
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
    circuit_json = bell_circuit.model_dump(mode="json")

    # 1. Verification SLA (< 1000ms on local test environment)
    t0 = time.perf_counter()
    res_verify = client.post("/api/circuits/verify", json={"circuit": circuit_json, "shots": 512})
    t_verify = time.perf_counter() - t0
    assert res_verify.status_code == 200
    assert t_verify < 2.0  # Safe threshold for local test runs

    # 2. Optimization SLA (< 1000ms)
    t0 = time.perf_counter()
    res_opt = client.post("/api/ai/optimize", json={"circuit": circuit_json, "level": 2})
    t_opt = time.perf_counter() - t0
    assert res_opt.status_code == 200
    assert t_opt < 2.0

    # 3. Generation SLA (< 1000ms)
    t0 = time.perf_counter()
    res_gen = client.post("/api/ai/generate", json={"prompt": "Two-qubit Bell state", "shots": 512})
    t_gen = time.perf_counter() - t0
    assert res_gen.status_code == 200
    assert t_gen < 2.0
