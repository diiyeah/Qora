from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.context_builder import CircuitContextBuilder


def sample_circuit() -> Circuit:
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


def test_build_context_with_simulation() -> None:
    c = sample_circuit()
    ctx = CircuitContextBuilder.build_context(
        query="What state does this circuit prepare?",
        circuit=c,
        expected_behavior="Bell state |Phi+>",
        backend="aer",
        simulate_if_present=True,
        shots=512,
        seed=10,
    )

    assert ctx.analysis is not None
    assert ctx.analysis.gate_count == 2
    assert ctx.distribution is not None
    assert "00" in ctx.distribution
    assert "11" in ctx.distribution
    assert ctx.evidence is not None
    assert ctx.evidence.gate_count == 2

    # Check formatted prompts
    user_prompt = ctx.to_user_prompt()
    assert "What state does this circuit prepare?" in user_prompt
    assert "Circuit Analysis Metrics" in user_prompt
    assert "Simulation Measurement Distribution" in user_prompt
    assert "Bell state |Phi+>" in user_prompt

    sys_prompt = ctx.to_system_prompt()
    assert "CRITICAL PRINCIPLES" in sys_prompt
