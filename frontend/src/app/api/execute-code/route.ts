import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Simulate syntax error for demo if code contains "error"
    if (body.code && body.code.includes('error')) {
      return NextResponse.json(
        { 
          error: { 
            type: "syntax", 
            line: body.code.split('\n').findIndex((l: string) => l.includes('error')) + 1, 
            message: "Syntax error in quantum code", 
            details: {} 
          } 
        },
        { status: 400 }
      );
    }

    // Return a mock schema and results
    return NextResponse.json({
      circuit: {
        num_qubits: 2,
        num_clbits: 2,
        gates: [
          { name: "h", qubits: [0], layer: 0 },
          { name: "cx", qubits: [0, 1], layer: 1 }
        ],
        measurements: [
          { qubit: 0, clbit: 0 },
          { qubit: 1, clbit: 1 }
        ]
      },
      results: {
        counts: { "00": 512, "11": 512 },
        probabilities: { "00": 0.5, "11": 0.5 },
        statevector: [[0.707, 0], [0, 0], [0, 0], [0.707, 0]],
        backend_info: { name: "mock_execution", shots: body.shots || 1024 }
      }
    });
  } catch (error) {
    return NextResponse.json(
      { error: { type: "invalid_request", message: "Failed to parse request" } },
      { status: 400 }
    );
  }
}
