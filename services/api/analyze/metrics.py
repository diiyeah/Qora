from packages.schema.models import Circuit

def analyze_circuit(circuit: Circuit) -> dict:
    """Analyze a circuit and return its metrics."""
    
    metrics = {
        "total_gates": len(circuit.gates),
        "qubits": circuit.num_qubits,
        "depth": 0,
        "cnot_count": 0,
        "single_qubit_gates": 0,
        "two_qubit_gates": 0,
        "gate_types": {}
    }
    
    # Calculate gate types and counts
    for gate in circuit.gates:
        name = gate.name.lower()
        
        # Track gate types
        metrics["gate_types"][name] = metrics["gate_types"].get(name, 0) + 1
        
        # Track CNOTs specifically
        if name in ['cx', 'cnot']:
            metrics["cnot_count"] += 1
            
        # Track single vs two qubit gates
        if len(gate.qubits) == 1:
            metrics["single_qubit_gates"] += 1
        elif len(gate.qubits) == 2:
            metrics["two_qubit_gates"] += 1
            
        # Calculate max depth (simple layer estimation)
        if hasattr(gate, 'layer') and gate.layer is not None:
            metrics["depth"] = max(metrics["depth"], gate.layer + 1)
            
    # If layers aren't strictly defined, Qiskit's depth() would be used in a real implementation
    # qc = schema_to_qiskit(circuit)
    # metrics["depth"] = qc.depth()
    
    return {"metrics": metrics}
