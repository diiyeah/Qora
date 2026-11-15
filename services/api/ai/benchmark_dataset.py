"""Fault-injected benchmark dataset generator for QORA Phase 2 evaluation."""

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
from typing import Any, Literal

from packages.schema.ai import (
    BenchmarkDataset,
    BenchmarkRecord,
    ErrorCategory,
    FaultInjectionType,
)
from packages.schema.models import Circuit, CircuitMetadata, Gate, Measurement
from services.api.tools.circuit_ops import get_measurement_distribution


def get_base_circuits() -> dict[str, tuple[Circuit, str]]:
    """Library of reference canonical quantum circuits and their behavioral specifications."""
    circuits: dict[str, tuple[Circuit, str]] = {}

    # 1. Two-qubit Bell State |Φ+>
    circuits["bell_state"] = (
        Circuit(
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
        ),
        "Two-qubit Bell state with 50/50 superposition of |00> and |11>",
    )

    # 2. Three-qubit GHZ State |GHZ>
    circuits["ghz_state"] = (
        Circuit(
            num_qubits=3,
            num_clbits=3,
            gates=[
                Gate(name="h", qubits=[0], params=[], layer=0),
                Gate(name="cx", qubits=[0, 1], params=[], layer=1),
                Gate(name="cx", qubits=[1, 2], params=[], layer=2),
            ],
            measurements=[
                Measurement(qubit=0, clbit=0),
                Measurement(qubit=1, clbit=1),
                Measurement(qubit=2, clbit=2),
            ],
            metadata=CircuitMetadata(framework="qiskit"),
        ),
        "Three-qubit GHZ entangled state |000> + |111>",
    )

    # 3. Superposition on 3 qubits
    circuits["superposition_3"] = (
        Circuit(
            num_qubits=3,
            num_clbits=3,
            gates=[
                Gate(name="h", qubits=[0], params=[], layer=0),
                Gate(name="h", qubits=[1], params=[], layer=1),
                Gate(name="h", qubits=[2], params=[], layer=2),
            ],
            measurements=[
                Measurement(qubit=0, clbit=0),
                Measurement(qubit=1, clbit=1),
                Measurement(qubit=2, clbit=2),
            ],
            metadata=CircuitMetadata(framework="qiskit"),
        ),
        "Equal superposition across 3 qubits (8 uniform outcomes)",
    )

    # 4. Two-qubit Quantum Swap
    circuits["quantum_swap"] = (
        Circuit(
            num_qubits=2,
            num_clbits=2,
            gates=[
                Gate(name="x", qubits=[0], params=[], layer=0),
                Gate(name="cx", qubits=[0, 1], params=[], layer=1),
                Gate(name="cx", qubits=[1, 0], params=[], layer=2),
                Gate(name="cx", qubits=[0, 1], params=[], layer=3),
            ],
            measurements=[
                Measurement(qubit=0, clbit=0),
                Measurement(qubit=1, clbit=1),
            ],
            metadata=CircuitMetadata(framework="qiskit"),
        ),
        "Quantum swap circuit exchanging state of qubit 0 and qubit 1",
    )

    # 5. Phase rotation circuit
    circuits["phase_rotation"] = (
        Circuit(
            num_qubits=1,
            num_clbits=1,
            gates=[
                Gate(name="h", qubits=[0], params=[], layer=0),
                Gate(name="rz", qubits=[0], params=[round(math.pi / 2, 4)], layer=1),
                Gate(name="h", qubits=[0], params=[], layer=2),
            ],
            measurements=[Measurement(qubit=0, clbit=0)],
            metadata=CircuitMetadata(framework="qiskit"),
        ),
        "Single qubit interference with pi/2 phase rotation",
    )

    # 6. Deutsch-Jozsa balanced oracle fragment
    circuits["deutsch_jozsa"] = (
        Circuit(
            num_qubits=2,
            num_clbits=1,
            gates=[
                Gate(name="x", qubits=[1], params=[], layer=0),
                Gate(name="h", qubits=[0], params=[], layer=1),
                Gate(name="h", qubits=[1], params=[], layer=2),
                Gate(name="cx", qubits=[0, 1], params=[], layer=3),
                Gate(name="h", qubits=[0], params=[], layer=4),
            ],
            measurements=[Measurement(qubit=0, clbit=0)],
            metadata=CircuitMetadata(framework="qiskit"),
        ),
        "Deutsch-Jozsa 1-bit balanced oracle identifying non-constant function",
    )

    return circuits


class FaultInjector:
    """Injects 6 canonical fault types into valid quantum circuits (Section 9.2)."""

    @classmethod
    def remove_gate(cls, circuit: Circuit, target_idx: int = 0) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        idx = max(0, min(target_idx, len(circuit.gates) - 1))
        new_gates = [g.model_copy() for i, g in enumerate(circuit.gates) if i != idx]
        removed_gate = circuit.gates[idx]
        for l_idx, g in enumerate(new_gates):
            g.layer = l_idx

        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=new_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "algorithmic",
            {"removed_gate": removed_gate.name, "target_qubits": removed_gate.qubits, "index": idx},
        )

    @classmethod
    def replace_gate(cls, circuit: Circuit, target_idx: int = 0) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        idx = max(0, min(target_idx, len(circuit.gates) - 1))
        new_gates = [g.model_copy() for g in circuit.gates]
        orig_gate = new_gates[idx]

        # Replace with incorrect gate
        replacement_name: Literal["h", "x", "y", "z", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "p", "cx", "cz", "swap", "ccx"] = (
            "z" if orig_gate.name in ("x", "h") else "x"
        )
        if len(orig_gate.qubits) > 1:
            replacement_name = "swap" if orig_gate.name == "cx" else "cx"

        new_gates[idx] = Gate(
            name=replacement_name,
            qubits=orig_gate.qubits,
            params=orig_gate.params,
            layer=orig_gate.layer,
        )

        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=new_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "invalid_gate",
            {
                "original_gate": orig_gate.name,
                "replacement_gate": replacement_name,
                "target_qubits": orig_gate.qubits,
                "index": idx,
            },
        )

    @classmethod
    def change_parameter(cls, circuit: Circuit, target_idx: int | None = None) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        # Find parameterized gate or pick first gate and add wrong angle
        param_idx = None
        for i, g in enumerate(circuit.gates):
            if g.params and len(g.params) > 0:
                param_idx = i
                break

        new_gates = [g.model_copy() for g in circuit.gates]
        if param_idx is not None:
            orig = new_gates[param_idx]
            old_param = orig.params[0]
            perturbed_param = round(old_param + math.pi / 4, 4)
            new_gates[param_idx] = Gate(
                name=orig.name,
                qubits=orig.qubits,
                params=[perturbed_param],
                layer=orig.layer,
            )
            faulty = Circuit(
                num_qubits=circuit.num_qubits,
                num_clbits=circuit.num_clbits,
                gates=new_gates,
                measurements=[m.model_copy() for m in circuit.measurements],
                metadata=circuit.metadata.model_copy(),
            )
            return (
                faulty,
                "parameter",
                {"gate": orig.name, "old_param": old_param, "new_param": perturbed_param, "index": param_idx},
            )

        # If no parameterized gate, turn first gate into perturbed rotation
        idx = 0
        orig = new_gates[idx]
        new_gates[idx] = Gate(
            name="rx",
            qubits=orig.qubits[:1],
            params=[round(math.pi / 3, 4)],
            layer=orig.layer,
        )
        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=new_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "parameter",
            {"gate": "rx", "new_param": round(math.pi / 3, 4), "index": idx},
        )

    @classmethod
    def change_qubit_mapping(cls, circuit: Circuit, target_idx: int | None = None) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        # Invert control/target on multi-qubit gate, or remap 1-qubit gate
        multi_idx = None
        for i, g in enumerate(circuit.gates):
            if len(g.qubits) >= 2:
                multi_idx = i
                break

        new_gates = [g.model_copy() for g in circuit.gates]
        if multi_idx is not None:
            orig = new_gates[multi_idx]
            reversed_qubits = list(reversed(orig.qubits))
            new_gates[multi_idx] = Gate(
                name=orig.name,
                qubits=reversed_qubits,
                params=orig.params,
                layer=orig.layer,
            )
            faulty = Circuit(
                num_qubits=circuit.num_qubits,
                num_clbits=circuit.num_clbits,
                gates=new_gates,
                measurements=[m.model_copy() for m in circuit.measurements],
                metadata=circuit.metadata.model_copy(),
            )
            return (
                faulty,
                "qubit_mapping",
                {"gate": orig.name, "old_qubits": orig.qubits, "new_qubits": reversed_qubits, "index": multi_idx},
            )

        # Single qubit circuit: remap to out of bounds or unused qubit
        idx = 0
        orig = new_gates[idx]
        new_qubits = [(orig.qubits[0] + 1) % circuit.num_qubits]
        new_gates[idx] = Gate(
            name=orig.name,
            qubits=new_qubits,
            params=orig.params,
            layer=orig.layer,
        )
        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=new_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "qubit_mapping",
            {"gate": orig.name, "old_qubits": orig.qubits, "new_qubits": new_qubits, "index": idx},
        )

    @classmethod
    def reorder_gates(cls, circuit: Circuit) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        # Swap gate 0 and gate 1
        if len(circuit.gates) < 2:
            return cls.remove_gate(circuit, 0)

        new_gates = [g.model_copy() for g in circuit.gates]
        new_gates[0], new_gates[1] = new_gates[1], new_gates[0]
        new_gates[0].layer, new_gates[1].layer = 0, 1

        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=new_gates,
            measurements=[m.model_copy() for m in circuit.measurements],
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "gate_ordering",
            {"swapped_indices": [0, 1], "gates": [new_gates[1].name, new_gates[0].name]},
        )

    @classmethod
    def remove_measurement(cls, circuit: Circuit) -> tuple[Circuit, ErrorCategory, dict[str, Any]]:
        faulty = Circuit(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            gates=[g.model_copy() for g in circuit.gates],
            measurements=[],  # dropped all measurements
            metadata=circuit.metadata.model_copy(),
        )
        return (
            faulty,
            "measurement",
            {"action": "dropped_all_measurements", "original_count": len(circuit.measurements)},
        )


class BenchmarkDatasetGenerator:
    """Generates and manages the fault-injected evaluation benchmark suite."""

    FAULT_TYPES: list[FaultInjectionType] = [
        "remove_gate",
        "replace_gate",
        "change_parameter",
        "change_qubit_mapping",
        "reorder_gates",
        "remove_measurement",
    ]

    @classmethod
    def generate(cls) -> BenchmarkDataset:
        base_circuits = get_base_circuits()
        records: list[BenchmarkRecord] = []
        rec_index = 0

        for c_key, (original_circuit, expected_behavior) in base_circuits.items():
            expected_dist = get_measurement_distribution(original_circuit, shots=1024, seed=42)

            for f_type in cls.FAULT_TYPES:
                rec_index += 1
                circuit_id = f"qora-bench-{c_key}-{f_type}"

                # Inject fault
                if f_type == "remove_gate":
                    faulty, err_cat, loc = FaultInjector.remove_gate(original_circuit, 0)
                elif f_type == "replace_gate":
                    faulty, err_cat, loc = FaultInjector.replace_gate(original_circuit, 0)
                elif f_type == "change_parameter":
                    faulty, err_cat, loc = FaultInjector.change_parameter(original_circuit)
                elif f_type == "change_qubit_mapping":
                    faulty, err_cat, loc = FaultInjector.change_qubit_mapping(original_circuit)
                elif f_type == "reorder_gates":
                    faulty, err_cat, loc = FaultInjector.reorder_gates(original_circuit)
                elif f_type == "remove_measurement":
                    faulty, err_cat, loc = FaultInjector.remove_measurement(original_circuit)
                else:
                    faulty, err_cat, loc = FaultInjector.remove_gate(original_circuit, 0)

                # Deterministic split: 33% development, 67% held-out
                split: Literal["development", "held_out"] = "development" if (rec_index % 3 == 0) else "held_out"

                record = BenchmarkRecord(
                    circuit_id=circuit_id,
                    name=f"{c_key} with injected {f_type}",
                    original_circuit=original_circuit,
                    faulty_circuit=faulty,
                    fault_type=f_type,
                    error_category=err_cat,
                    fault_location=loc,
                    expected_behavior=expected_behavior,
                    expected_distribution=expected_dist,
                    actual_behavior=f"Injected {f_type} fault causing erroneous quantum state.",
                    corrected_circuit=original_circuit,
                    split=split,
                )
                records.append(record)

        summary = {
            "total_records": len(records),
            "development_records": sum(1 for r in records if r.split == "development"),
            "held_out_records": sum(1 for r in records if r.split == "held_out"),
            "unique_base_circuits": len(base_circuits),
            "unique_fault_types": len(cls.FAULT_TYPES),
        }

        return BenchmarkDataset(
            records=records,
            created_at=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            summary=summary,
        )

    @classmethod
    def save_to_file(cls, dataset: BenchmarkDataset, file_path: str = "data/benchmarks/benchmark_dataset.json") -> str:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(dataset.model_dump_json(indent=2))
        return str(path.resolve())

    @classmethod
    def load_from_file(cls, file_path: str = "data/benchmarks/benchmark_dataset.json") -> BenchmarkDataset:
        path = Path(file_path)
        if not path.exists():
            ds = cls.generate()
            cls.save_to_file(ds, file_path)
            return ds
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BenchmarkDataset.model_validate(data)
