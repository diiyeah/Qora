import json
from pathlib import Path

from packages.schema.ai import BenchmarkDataset
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.ai.benchmark_dataset import (
    BenchmarkDatasetGenerator,
    FaultInjector,
    get_base_circuits,
)


def sample_test_circuit() -> Circuit:
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


def test_fault_injector_remove_gate() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.remove_gate(c, 0)
    assert len(faulty.gates) == 1
    assert cat == "algorithmic"
    assert loc["removed_gate"] == "h"


def test_fault_injector_replace_gate() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.replace_gate(c, 0)
    assert len(faulty.gates) == 2
    assert cat == "invalid_gate"
    assert faulty.gates[0].name != "h"


def test_fault_injector_change_parameter() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.change_parameter(c)
    assert cat == "parameter"
    assert "new_param" in loc


def test_fault_injector_change_qubit_mapping() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.change_qubit_mapping(c)
    assert cat == "qubit_mapping"
    assert faulty.gates[1].qubits == [1, 0]


def test_fault_injector_reorder_gates() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.reorder_gates(c)
    assert cat == "gate_ordering"
    assert faulty.gates[0].name == "cx"
    assert faulty.gates[1].name == "h"


def test_fault_injector_remove_measurement() -> None:
    c = sample_test_circuit()
    faulty, cat, loc = FaultInjector.remove_measurement(c)
    assert cat == "measurement"
    assert len(faulty.measurements) == 0


def test_generate_benchmark_dataset() -> None:
    ds = BenchmarkDatasetGenerator.generate()
    assert isinstance(ds, BenchmarkDataset)
    assert len(ds.records) > 0
    assert ds.summary["total_records"] == len(ds.records)
    assert ds.summary["development_records"] > 0
    assert ds.summary["held_out_records"] > 0

    # Ensure all 6 fault types appear
    fault_types = {r.fault_type for r in ds.records}
    assert len(fault_types) == 6


def test_benchmark_dataset_save_and_load(tmp_path: Path) -> None:
    ds = BenchmarkDatasetGenerator.generate()
    file_path = str(tmp_path / "test_benchmark.json")
    saved_path = BenchmarkDatasetGenerator.save_to_file(ds, file_path)
    assert Path(saved_path).exists()

    loaded = BenchmarkDatasetGenerator.load_from_file(file_path)
    assert len(loaded.records) == len(ds.records)
    assert loaded.version == ds.version
