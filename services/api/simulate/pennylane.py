from typing import Any
try:
    import pennylane as qml
except ImportError:
    qml = None
from importlib.metadata import version
from services.api.simulate.base import BackendAdapter
from packages.schema.models import Circuit
from services.api.errors import PlatformError

class PennyLaneAdapter(BackendAdapter):
    @property
    def name(self) -> str:
        return "pennylane_default.qubit"
        
    def capabilities(self) -> dict[str, Any]:
        return {
            "max_qubits": 20,
            "supports_statevector": True,
            "supports_noise": False
        }
        
    def run(self, circuit: Circuit, shots: int = 1024, noise: dict[str, Any] | None = None, seed: int | None = None) -> dict[str, Any]:
        if qml is None:
            raise PlatformError("backend_unavailable", "PennyLane is not installed in the current environment.")
        if noise:
            raise PlatformError("backend_unavailable", "PennyLane adapter does not currently support noise models.")
            
        dev = qml.device('default.qubit', wires=circuit.num_qubits, shots=shots)
        
        @qml.qnode(dev)  # type: ignore[untyped-decorator]
        def qnode_circuit() -> Any:
            # Translate gates
            for gate in circuit.gates:
                name = gate.name.lower()
                qubits = gate.qubits
                params = gate.params or []
                
                # Simple mapping (a full implementation would map all supported gates)
                if name == 'h':
                    qml.Hadamard(wires=qubits[0])
                elif name == 'x':
                    qml.PauliX(wires=qubits[0])
                elif name == 'cx' or name == 'cnot':
                    qml.CNOT(wires=[qubits[0], qubits[1]])
                elif name == 'rx':
                    qml.RX(params[0], wires=qubits[0])
                elif name == 'ry':
                    qml.RY(params[0], wires=qubits[0])
                elif name == 'rz':
                    qml.RZ(params[0], wires=qubits[0])
                else:
                    raise PlatformError("invalid_gate", f"Gate {name} not mapped in PennyLane adapter yet.")
                    
            # In Pennylane, if you return qml.counts(), it calculates based on all wires
            if circuit.measurements:
                meas_wires = [m.qubit for m in circuit.measurements]
                return qml.counts(wires=meas_wires)
            return qml.counts(wires=range(circuit.num_qubits))
            
        try:
            raw_counts = qnode_circuit()
            
            # Bit-ordering normalization:
            # Qiskit output puts qubit 0 on the far right (little-endian: q_n...q_1q_0).
            # PennyLane output puts qubit 0 on the far left (big-endian: q_0q_1...q_n).
            # To make PennyLane match Qiskit's standard, we must reverse the bitstrings.
            normalized_counts: dict[str, int] = {}
            for bitstring, count in raw_counts.items():
                reversed_bitstring = bitstring[::-1]
                normalized_counts[reversed_bitstring] = int(count)
                
            return {
                "counts": normalized_counts,
                "backend": {
                    "name": self.name,
                    "version": version("pennylane"),
                    "framework": "pennylane",
                    "framework_version": version("pennylane")
                }
            }
        except Exception as e:
            raise PlatformError("backend_unavailable", f"PennyLane simulation failed: {str(e)}")
