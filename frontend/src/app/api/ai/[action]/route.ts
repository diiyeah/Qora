import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ action: string }> }
) {
  try {
    const { action } = await params;
    const body = await request.json();

    if (body.circuit && typeof body.circuit === 'object') {
      if (!body.circuit.metadata) {
        body.circuit.metadata = { framework: 'qiskit', task_id: null };
      }
      if (!Array.isArray(body.circuit.gates)) {
        body.circuit.gates = [];
      } else {
        body.circuit.gates = body.circuit.gates.map((g: any, idx: number) => ({
          name: g.name,
          qubits: g.qubits || [],
          params: g.params || [],
          layer: g.layer ?? idx,
        }));
      }
      if (!Array.isArray(body.circuit.measurements)) {
        body.circuit.measurements = [];
      }
    }

    const backendRes = await fetch(`${BACKEND_URL}/api/ai/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const rawText = await backendRes.text();
    try {
      const data = JSON.parse(rawText);
      return NextResponse.json(data, { status: backendRes.status });
    } catch {
      return NextResponse.json(
        { error: { type: 'backend_response_error', message: rawText || 'Invalid response from quantum backend' } },
        { status: backendRes.status || 500 }
      );
    }
  } catch (error: any) {
    return NextResponse.json(
      {
        error: {
          type: 'gateway_error',
          message: `Unable to connect to Quantum Backend at ${BACKEND_URL}: ${error.message || 'Connection failed'}`,
        },
      },
      { status: 502 }
    );
  }
}
