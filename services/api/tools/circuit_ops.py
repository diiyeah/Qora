"""Deterministic quantum operations and metrics engine for QORA."""

from collections import Counter
from importlib.metadata import version
from typing import cast

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from packages.schema.ai import CircuitAnalysis, CircuitComparison
from packages.schema.api import BackendInfo, SimulationResult
from packages.schema.models import Circuit
from services.api.convert import circuit_to_qiskit
from services.api.errors import PlatformError


def analyze_circuit(circuit: Circuit) -> CircuitAnalysis:
    """Analyze circuit structure, depth, and gate distributions."""
    qc = circuit_to_qiskit(circuit)
    counts = Counter(gate.name for gate in circuit.gates)
    multi_qubit = sum(1 for gate in circuit.gates if len(gate.qubits) > 1)
    gate_depth = qc.depth(filter_function=lambda x: x.operation.name != "measure")

    return CircuitAnalysis(
        qubit_count=circuit.num_qubits,
        clbit_count=circuit.num_clbits,
        depth=gate_depth,
        gate_count=len(circuit.gates),
        cnot_count=counts.get("cx", 0),
        multi_qubit_gates=multi_qubit,
        gate_breakdown={str(k): int(v) for k, v in counts.items()},
    )


def simulate_circuit(
    circuit: Circuit,
    shots: int = 1024,
    seed: int | None = None,
) -> SimulationResult:
    """Execute a canonical circuit on AerSimulator with wire 0 on the left."""
    qc = circuit_to_qiskit(circuit)

    # If circuit has no measurements, measure all qubits to classical bits
    if not circuit.measurements:
        if qc.num_clbits < qc.num_qubits:
            measured_qc = QuantumCircuit(qc.num_qubits, qc.num_qubits)
            for inst in qc.data:
                measured_qc.append(inst.operation, inst.qubits, inst.clbits)
            qc = measured_qc
        qc.measure(range(circuit.num_qubits), range(circuit.num_qubits))

    try:
        simulator = AerSimulator(max_parallel_threads=1)
        result = simulator.run(qc, shots=shots, seed_simulator=seed).result()
        if not result.success:
            raise PlatformError(
                "backend_unavailable", "Aer could not complete the simulation.",
                status_code=503,
            )
        counts = result.get_counts()
        reversed_counts = {
            str(bits).replace(" ", "")[::-1]: int(count)
            for bits, count in counts.items()
        }
        return SimulationResult(
            counts=reversed_counts,
            shots=shots,
            seed=seed,
            backend=BackendInfo(
                name="aer",
                version=version("qiskit-aer"),
                framework="qiskit",
                framework_version=version("qiskit"),
            ),
        )
    except PlatformError:
        raise
    except Exception as exc:
        raise PlatformError(
            "backend_unavailable", f"Aer simulation failed: {exc}",
            status_code=503,
        ) from None


def get_measurement_distribution(
    circuit: Circuit,
    shots: int = 1024,
    seed: int | None = None,
) -> dict[str, float]:
    """Retrieve normalized measurement probabilities from simulated counts."""
    res = simulate_circuit(circuit, shots=shots, seed=seed)
    total_shots = res.shots
    return {
        bits: round(count / total_shots, 4)
        for bits, count in sorted(res.counts.items())
    }


def get_statevector(circuit: Circuit) -> dict[str, str]:
    """Retrieve non-zero basis state amplitudes for the circuit before measurement."""
    # Build circuit without measurement operations for pure statevector evaluation
    qc = QuantumCircuit(circuit.num_qubits)
    for gate in circuit.gates:
        name = gate.name
        q = gate.qubits
        p = gate.params
        if name == "h":
            qc.h(q[0])
        elif name == "x":
            qc.x(q[0])
        elif name == "y":
            qc.y(q[0])
        elif name == "z":
            qc.z(q[0])
        elif name == "s":
            qc.s(q[0])
        elif name == "sdg":
            qc.sdg(q[0])
        elif name == "t":
            qc.t(q[0])
        elif name == "tdg":
            qc.tdg(q[0])
        elif name == "rx":
            qc.rx(p[0], q[0])
        elif name == "ry":
            qc.ry(p[0], q[0])
        elif name == "rz":
            qc.rz(p[0], q[0])
        elif name == "p":
            qc.p(p[0], q[0])
        elif name == "cx":
            qc.cx(q[0], q[1])
        elif name == "cz":
            qc.cz(q[0], q[1])
        elif name == "swap":
            qc.swap(q[0], q[1])
        elif name == "ccx":
            qc.ccx(q[0], q[1], q[2])

    try:
        sv = Statevector.from_instruction(qc)
        sv_dict = sv.to_dict()
        amplitudes: dict[str, str] = {}
        for bitstring, val in sv_dict.items():
            cval = complex(val)
            if abs(cval) > 1e-5:
                # Reverse bitstring so wire 0 is on the left
                rev_bits = str(bitstring)[::-1]
                real_part = round(cval.real, 4)
                imag_part = round(cval.imag, 4)
                if abs(imag_part) < 1e-5:
                    amplitudes[rev_bits] = f"{real_part:+.4f}"
                else:
                    amplitudes[rev_bits] = f"{real_part:+.4f}{imag_part:+.4f}j"
        return dict(sorted(amplitudes.items()))
    except Exception as exc:
        raise PlatformError(
            "backend_unavailable", f"Statevector calculation failed: {exc}",
            status_code=503,
        ) from None


def calculate_metrics(circuit: Circuit) -> dict[str, int]:
    """Calculate core circuit metrics."""
    analysis = analyze_circuit(circuit)
    return {
        "qubit_count": analysis.qubit_count,
        "clbit_count": analysis.clbit_count,
        "depth": analysis.depth,
        "gate_count": analysis.gate_count,
        "cnot_count": analysis.cnot_count,
        "multi_qubit_gates": analysis.multi_qubit_gates,
    }


def compare_circuits(circuit_a: Circuit, circuit_b: Circuit) -> CircuitComparison:
    """Compare two circuits on resource metrics and execution behavior."""
    analysis_a = analyze_circuit(circuit_a)
    analysis_b = analyze_circuit(circuit_b)

    dist_a = get_measurement_distribution(circuit_a, shots=2048, seed=42)
    dist_b = get_measurement_distribution(circuit_b, shots=2048, seed=42)

    # Compute Total Variation Distance (TVD): 0.5 * sum(|p_a(x) - p_b(x)|)
    all_keys = set(dist_a.keys()) | set(dist_b.keys())
    tvd = 0.5 * sum(abs(dist_a.get(k, 0.0) - dist_b.get(k, 0.0)) for k in all_keys)

    equivalent = tvd < 0.06

    return CircuitComparison(
        equivalent=equivalent,
        gate_count_diff=analysis_b.gate_count - analysis_a.gate_count,
        depth_diff=analysis_b.depth - analysis_a.depth,
        cnot_diff=analysis_b.cnot_count - analysis_a.cnot_count,
        distribution_distance=round(tvd, 4),
    )
