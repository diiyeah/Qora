import pytest

from services.api.ai.generator import NaturalLanguageCircuitGenerator


def test_generate_bell_state_verification() -> None:
    generator = NaturalLanguageCircuitGenerator()
    res = generator.generate("Create a two-qubit Bell state", shots=2048, seed=42)

    assert res.circuit.num_qubits == 2
    assert res.circuit.num_clbits == 2
    assert len(res.circuit.gates) == 2
    assert res.circuit.gates[0].name == "h"
    assert res.circuit.gates[1].name == "cx"
    assert len(res.circuit.measurements) == 2

    # Verification criteria from spec: approx 50% |00> and approx 50% |11>
    assert "00" in res.distribution
    assert "11" in res.distribution
    assert abs(res.distribution["00"] - 0.5) < 0.1
    assert abs(res.distribution["11"] - 0.5) < 0.1
    assert res.validation_passed is True
    assert res.evidence.cnot_count == 1
    assert res.evidence.depth == 2


def test_generate_ghz_state() -> None:
    generator = NaturalLanguageCircuitGenerator()
    res = generator.generate("Generate a 3-qubit GHZ state", shots=2048, seed=42)

    assert res.circuit.num_qubits == 3
    assert res.circuit.num_clbits == 3
    assert len(res.circuit.gates) == 3
    assert res.circuit.gates[0].name == "h"
    assert res.circuit.gates[1].name == "cx"
    assert res.circuit.gates[2].name == "cx"

    assert "000" in res.distribution
    assert "111" in res.distribution
    assert abs(res.distribution["000"] - 0.5) < 0.1
    assert abs(res.distribution["111"] - 0.5) < 0.1
    assert res.validation_passed is True


def test_generate_superposition_register() -> None:
    generator = NaturalLanguageCircuitGenerator()
    res = generator.generate("Create superposition on 3 qubits", shots=1024, seed=42)

    assert res.circuit.num_qubits == 3
    assert len(res.circuit.gates) == 3
    assert all(g.name == "h" for g in res.circuit.gates)
    assert len(res.distribution) == 8  # 2^3 basis states
    assert res.validation_passed is True


def test_generate_swap_circuit() -> None:
    generator = NaturalLanguageCircuitGenerator()
    res = generator.generate("Build a quantum swap circuit", shots=512, seed=42)

    assert res.circuit.num_qubits == 2
    assert any(g.name == "swap" for g in res.circuit.gates)
