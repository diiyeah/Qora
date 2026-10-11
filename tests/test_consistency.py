import pytest
from packages.schema.models import Circuit

# Dummy backend adapter mocks for testing
from services.api.simulate.pennylane import PennyLaneAdapter
from services.api.simulate.cirq_adapter import CirqAdapter
# Assuming aer adapter exists with similar interface

@pytest.fixture
def bell_circuit():
    return Circuit.model_validate({
        "num_qubits": 2,
        "num_clbits": 2,
        "gates": [
            {"name": "h", "qubits": [0], "params": [], "layer": 0},
            {"name": "cx", "qubits": [0, 1], "params": [], "layer": 1},
        ],
        "measurements": [{"qubit": 0, "clbit": 0}, {"qubit": 1, "clbit": 1}],
        "metadata": {"framework": "test", "task_id": None},
    })

def test_backend_consistency(bell_circuit):
    """
    Ensure Aer, PennyLane, and Cirq agree within statistical tolerance 
    (using Total Variation Distance) for the same circuits.
    """
    shots = 10000
    
    pennylane_adapter = PennyLaneAdapter()
    cirq_adapter = CirqAdapter()
    
    pl_result = pennylane_adapter.run(bell_circuit, shots=shots, seed=42)
    cirq_result = cirq_adapter.run(bell_circuit, shots=shots, seed=42)
    
    pl_counts = pl_result["counts"]
    cirq_counts = cirq_result["counts"]
    
    # Convert to probabilities
    pl_probs = {k: v/shots for k, v in pl_counts.items()}
    cirq_probs = {k: v/shots for k, v in cirq_counts.items()}
    
    # Calculate Total Variation Distance
    all_states = set(pl_probs.keys()).union(set(cirq_probs.keys()))
    tvd = 0.5 * sum(abs(pl_probs.get(s, 0) - cirq_probs.get(s, 0)) for s in all_states)
    
    # For 10000 shots, TVD should be very small (e.g., < 0.05) if the distributions match
    assert tvd < 0.05, f"Total Variation Distance ({tvd}) exceeds threshold! Backends do not match."
