import pytest

from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.tools.circuit_ops import (
    analyze_circuit,
    calculate_metrics,
    compare_circuits,
    get_measurement_distribution,
    get_statevector,
    simulate_circuit,
)
from services.api.tools.registry import default_tool_registry


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


def test_analyze_circuit_metrics() -> None:
    c = bell_circuit()
    analysis = analyze_circuit(c)

    assert analysis.qubit_count == 2
    assert analysis.clbit_count == 2
    assert analysis.gate_count == 2
    assert analysis.cnot_count == 1
    assert analysis.depth == 2
    assert analysis.gate_breakdown == {"h": 1, "cx": 1}


def test_simulate_circuit_bell_distribution() -> None:
    c = bell_circuit()
    result = simulate_circuit(c, shots=2048, seed=42)

    assert sum(result.counts.values()) == 2048
    assert set(result.counts.keys()) == {"00", "11"}
    # Verify ~50% / ~50%
    assert abs(result.counts["00"] / 2048 - 0.5) < 0.05
    assert abs(result.counts["11"] / 2048 - 0.5) < 0.05


def test_get_measurement_distribution() -> None:
    c = bell_circuit()
    dist = get_measurement_distribution(c, shots=1000, seed=123)

    assert "00" in dist
    assert "11" in dist
    assert abs(dist["00"] + dist["11"] - 1.0) < 0.001


def test_get_statevector_bell() -> None:
    c = bell_circuit()
    sv = get_statevector(c)

    assert "00" in sv
    assert "11" in sv
    # Bell state amplitudes are 1/sqrt(2) approx +0.7071
    assert "+0.7071" in sv["00"]
    assert "+0.7071" in sv["11"]


def test_compare_circuits_identical_and_different() -> None:
    c1 = bell_circuit()
    c2 = bell_circuit()
    comp = compare_circuits(c1, c2)

    assert comp.equivalent is True
    assert comp.gate_count_diff == 0
    assert comp.distribution_distance is not None
    assert comp.distribution_distance < 0.05

    # Different circuit with an extra X gate
    c3 = Circuit(
        num_qubits=2,
        num_clbits=2,
        gates=[
            Gate(name="x", qubits=[0], params=[], layer=0),
            Gate(name="h", qubits=[0], params=[], layer=1),
            Gate(name="cx", qubits=[0, 1], params=[], layer=2),
        ],
        measurements=[
            Measurement(qubit=0, clbit=0),
            Measurement(qubit=1, clbit=1),
        ],
        metadata=CircuitMetadata(framework="qiskit"),
    )
    comp_diff = compare_circuits(c1, c3)
    assert comp_diff.gate_count_diff == 1


def test_registry_execute_tool() -> None:
    payload = bell_circuit().model_dump(mode="json")
    res = default_tool_registry.execute("analyze_circuit", {"circuit": payload})

    assert "error" not in res
    assert res.get("gate_count") == 2
    assert res.get("cnot_count") == 1
