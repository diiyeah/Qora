from typing import Any
from packages.schema.models import Circuit

def analyze_circuit(circuit: Circuit) -> dict[str, Any]:
    """Analyze a circuit and return its metrics."""
    gate_types: dict[str, int] = {}
    total_gates = len(circuit.gates)
    qubits = circuit.num_qubits
    depth = 0
    cnot_count = 0
    single_qubit_gates = 0
    two_qubit_gates = 0
    
    # Calculate gate types and counts
    for gate in circuit.gates:
        name = gate.name.lower()
        
        # Track gate types
        gate_types[name] = gate_types.get(name, 0) + 1
        
        # Track CNOTs specifically
        if name in ['cx', 'cnot']:
            cnot_count += 1
            
        # Track single vs two qubit gates
        if len(gate.qubits) == 1:
            single_qubit_gates += 1
        elif len(gate.qubits) == 2:
            two_qubit_gates += 1
            
        # Calculate max depth (simple layer estimation)
        if hasattr(gate, 'layer') and gate.layer is not None:
            depth = max(depth, gate.layer + 1)
            
    return {
        "metrics": {
            "total_gates": total_gates,
            "qubits": qubits,
            "depth": depth,
            "cnot_count": cnot_count,
            "single_qubit_gates": single_qubit_gates,
            "two_qubit_gates": two_qubit_gates,
            "gate_types": gate_types,
        }
    }
