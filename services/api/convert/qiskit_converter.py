"""Bidirectional converter between QORA canonical Circuit and Qiskit QuantumCircuit."""

from typing import cast

from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction

from packages.schema.models import Circuit, CircuitMetadata, Gate, GateName, Measurement
from services.api.errors import PlatformError

SUPPORTED_GATES: frozenset[str] = frozenset({
    "h", "x", "y", "z", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "p", "cx", "cz", "swap", "ccx",
})


def circuit_to_qiskit(circuit: Circuit) -> QuantumCircuit:
    """Convert a QORA canonical Circuit into a Qiskit QuantumCircuit."""
    qc = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)

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
        else:
            raise PlatformError(
                "invalid_gate", f"Unsupported gate '{name}'",
                details={"gate": name},
            )

    for m in circuit.measurements:
        qc.measure(m.qubit, m.clbit)

    return qc


def qiskit_to_circuit(qc: QuantumCircuit) -> Circuit:
    """Convert a Qiskit QuantumCircuit into a QORA canonical Circuit."""
    gates: list[Gate] = []
    measurements: list[Measurement] = []

    layer_counter = 0
    for instruction in qc.data:
        inst = cast(CircuitInstruction, instruction)
        op_name = inst.operation.name.lower()
        qubit_indices = [qc.find_bit(q).index for q in inst.qubits]
        clbit_indices = [qc.find_bit(c).index for c in inst.clbits]
        params = [float(p) for p in inst.operation.params]

        if op_name == "measure":
            if qubit_indices and clbit_indices:
                measurements.append(Measurement(qubit=qubit_indices[0], clbit=clbit_indices[0]))
            continue

        if op_name not in SUPPORTED_GATES:
            raise PlatformError(
                "invalid_gate", f"Gate '{op_name}' is not supported in QORA canonical schema",
                details={"gate": op_name},
            )

        gate_name = cast(GateName, op_name)
        gates.append(Gate(
            name=gate_name,
            qubits=qubit_indices,
            params=params,
            layer=layer_counter,
        ))
        layer_counter += 1

    return Circuit(
        num_qubits=qc.num_qubits,
        num_clbits=qc.num_clbits,
        gates=gates,
        measurements=measurements,
        metadata=CircuitMetadata(framework="qiskit"),
    )
