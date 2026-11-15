from packages.schema.ai import AIChatRequest, AIAnalyzeRequest
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.llm_client import MockLLMProvider
from services.api.ai.orchestrator import AIOrchestrator


def sample_bell() -> Circuit:
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


def test_ai_orchestrator_chat() -> None:
    orchestrator = AIOrchestrator(llm_provider=MockLLMProvider())
    req = AIChatRequest(
        query="Explain the action of the Hadamard and CNOT gates in this circuit.",
        circuit=sample_bell(),
        expected_behavior="Entangled state",
    )
    resp = orchestrator.chat(req)

    assert resp.response
    assert "Based on the quantum circuit analysis" in resp.response
    assert resp.evidence is not None
    assert resp.evidence.gate_count == 2
    assert resp.evidence.cnot_count == 1
    assert "00" in resp.evidence.measurement_distribution


def test_ai_orchestrator_analyze() -> None:
    orchestrator = AIOrchestrator(llm_provider=MockLLMProvider())
    req = AIAnalyzeRequest(
        circuit=sample_bell(),
        query="Analyze circuit properties",
    )
    resp = orchestrator.analyze(req)

    assert resp.analysis.gate_count == 2
    assert resp.analysis.depth == 2
    assert resp.analysis.cnot_count == 1
    assert "00" in resp.distribution
    assert resp.evidence.qubit_count == 2
    assert resp.explanation
