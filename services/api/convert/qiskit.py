from qiskit import QuantumCircuit
from packages.schema.models import Circuit

def schema_to_qiskit(circuit_schema: Circuit) -> QuantumCircuit:
    qc = QuantumCircuit(circuit_schema.num_qubits, circuit_schema.num_clbits)
    
    for gate in circuit_schema.gates:
        name = gate.name.lower()
        qubits = gate.qubits
        params = gate.params
        
        gate_method = getattr(qc, name, None)
        if not gate_method:
            raise ValueError(f"Unsupported gate: {name}")
            
        if params:
            gate_method(*params, *qubits)
        else:
            gate_method(*qubits)
            
    for meas in circuit_schema.measurements:
        qc.measure(meas.qubit, meas.clbit)
        
    return qc
