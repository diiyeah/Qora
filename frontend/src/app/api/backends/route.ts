import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    backends: [
      { id: "aer_simulator", name: "Aer Simulator", max_qubits: 30, supports_statevector: true, supports_noise: true },
      { id: "pennylane_default.qubit", name: "PennyLane Default", max_qubits: 20, supports_statevector: true, supports_noise: false },
      { id: "cirq_simulator", name: "Cirq Simulator", max_qubits: 20, supports_statevector: true, supports_noise: true },
      { id: "qbraid_local", name: "qBraid Local", max_qubits: 20, supports_statevector: true, supports_noise: true },
    ]
  });
}
