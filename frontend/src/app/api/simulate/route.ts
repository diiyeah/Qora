import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Mock response for /simulate
    const mockResponse = {
      counts: {
        "00": 512,
        "11": 512
      },
      probabilities: {
        "00": 0.5,
        "11": 0.5
      },
      statevector: [
        [0.70710678, 0],
        [0, 0],
        [0, 0],
        [0.70710678, 0]
      ],
      per_gate_states: [
        // Step 0: |00>
        [
          { theta: 0, phi: 0, r: 1 }, // q0
          { theta: 0, phi: 0, r: 1 }, // q1
        ],
        // Step 1: H on q0 -> |+0>
        [
          { theta: Math.PI / 2, phi: 0, r: 1 }, // q0
          { theta: 0, phi: 0, r: 1 },           // q1
        ],
        // Step 2: CX q0, q1 -> Bell state (entangled, mixed reduced state)
        [
          { theta: 0, phi: 0, r: 0 }, // q0 mixed
          { theta: 0, phi: 0, r: 0 }, // q1 mixed
        ]
      ],
      backend_info: {
        name: body.backend || "mock_simulator",
        shots: body.shots || 1024
      }
    };

    return NextResponse.json(mockResponse);
  } catch (error) {
    return NextResponse.json(
      { error: { type: "invalid_request", message: "Failed to parse request" } },
      { status: 400 }
    );
  }
}
