import cirq
from importlib.metadata import version
from services.api.simulate.base import BackendAdapter
from packages.schema.models import Circuit
from services.api.errors import PlatformError

class CirqAdapter(BackendAdapter):
    @property
    def name(self) -> str:
        return "cirq_simulator"
        
    def capabilities(self) -> dict:
        return {
            "max_qubits": 20,
            "supports_statevector": True,
            "supports_noise": True
        }
        
    def run(self, circuit: Circuit, shots: int = 1024, noise: dict | None = None, seed: int | None = None) -> dict:
        # Create qubits
        qubits = [cirq.LineQubit(i) for i in range(circuit.num_qubits)]
        c_circuit = cirq.Circuit()
        
        # Translate gates
        for gate in circuit.gates:
            name = gate.name.lower()
            q_idx = gate.qubits
            params = gate.params or []
            
            if name == 'h':
                c_circuit.append(cirq.H(qubits[q_idx[0]]))
            elif name == 'x':
                c_circuit.append(cirq.X(qubits[q_idx[0]]))
            elif name == 'cx' or name == 'cnot':
                c_circuit.append(cirq.CNOT(qubits[q_idx[0]], qubits[q_idx[1]]))
            else:
                raise PlatformError("invalid_gate", f"Gate {name} not mapped in Cirq adapter yet.")
                
        # Add measurements
        if circuit.measurements:
            for m in circuit.measurements:
                c_circuit.append(cirq.measure(qubits[m.qubit], key=str(m.clbit)))
                
        if noise:
            # Inject Cirq depolarization channel if requested
            c_circuit = c_circuit.with_noise(cirq.depolarize(p=noise.get('rate', 0.01)))
            
        simulator = cirq.Simulator(seed=seed)
        try:
            result = simulator.run(c_circuit, repetitions=shots)
            
            # Extract and normalize counts
            # Cirq returns a pandas DataFrame-like structure or a Counter.
            # We must parse it and ensure Qiskit bit-ordering (qubit 0 on the right)
            raw_counts = result.multi_measurement_histogram(keys=[str(i) for i in range(circuit.num_clbits)])
            
            normalized_counts = {}
            for bit_tuple, count in raw_counts.items():
                # bit_tuple is like (0, 1) for c0=0, c1=1. 
                # Qiskit expects "10" (c1 c0)
                bitstring = "".join(str(b) for b in reversed(bit_tuple))
                normalized_counts[bitstring] = count
                
            return {
                "counts": normalized_counts,
                "backend": {
                    "name": self.name,
                    "version": version("cirq"),
                    "framework": "cirq",
                    "framework_version": version("cirq")
                }
            }
        except Exception as e:
            raise PlatformError("backend_unavailable", f"Cirq simulation failed: {str(e)}")
