import axios from 'axios';

// Types derived from Phase 1 schema
export interface CircuitSchema {
  num_qubits: number;
  num_clbits: number;
  gates: Array<{
    name: string;
    qubits: number[];
    params?: number[];
    layer?: number;
  }>;
  measurements: Array<{
    qubit: number;
    clbit: number;
  }>;
  metadata?: {
    framework?: string;
    task_id?: string | null;
  };
}

export interface SimulateRequest {
  circuit: CircuitSchema;
  backend: string;
  shots: number;
  noise?: any;
}

export interface SimulateResponse {
  counts: Record<string, number>;
  probabilities: Record<string, number>;
  statevector: Array<[number, number]>;
  per_gate_states?: any;
  backend_info: any;
}

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const normalizeCircuit = (circuit?: CircuitSchema): CircuitSchema | undefined => {
  if (!circuit) return undefined;
  return {
    num_qubits: circuit.num_qubits || 2,
    num_clbits: circuit.num_clbits || 2,
    gates: (circuit.gates || []).map((g, idx) => ({
      name: g.name,
      qubits: g.qubits || [],
      params: g.params || [],
      layer: g.layer ?? idx,
    })),
    measurements: circuit.measurements || [],
    metadata: circuit.metadata || { framework: 'qiskit', task_id: null },
  };
};

export const QuantumAPI = {
  simulate: async (data: SimulateRequest): Promise<SimulateResponse> => {
    const response = await apiClient.post('/simulate', data);
    return response.data;
  },
  
  // Future endpoints placeholder
  executeCode: async (code: string, framework: string, shots: number) => {
    try {
      const response = await apiClient.post('/execute-code', { code, framework, shots });
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.error) {
        throw error.response.data.error;
      }
      throw error;
    }
  },
  
  convert: async (data: any, targetFormat: string) => {
    const payload = typeof data === 'string' ? { code: data, target_format: targetFormat } : { circuit: data, target_format: targetFormat };
    const response = await apiClient.post('/convert', payload);
    return response.data;
  },
  
  analyze: async (circuit: CircuitSchema) => {
    const response = await apiClient.post('/analyze', { circuit: normalizeCircuit(circuit) });
    return response.data;
  },
  
  getBackends: async () => {
    const response = await apiClient.get('/backends');
    return response.data;
  },

  aiChat: async (query: string, circuit?: CircuitSchema, expectedBehavior?: string) => {
    const response = await apiClient.post('/ai/chat', {
      query,
      circuit: normalizeCircuit(circuit),
      expected_behavior: expectedBehavior,
    });
    return response.data;
  },

  aiDiagnose: async (circuit?: CircuitSchema, sourceCode?: string, expectedBehavior?: string) => {
    const response = await apiClient.post('/ai/diagnose', {
      circuit: normalizeCircuit(circuit),
      source_code: sourceCode,
      expected_behavior: expectedBehavior,
    });
    return response.data;
  },

  aiGenerate: async (prompt: string) => {
    const response = await apiClient.post('/ai/generate', { prompt });
    return response.data;
  },

  aiAnalyze: async (circuit: CircuitSchema) => {
    const response = await apiClient.post('/ai/analyze', { circuit: normalizeCircuit(circuit) });
    return response.data;
  },

  aiRepair: async (
    circuit: CircuitSchema,
    sourceCode?: string,
    expectedBehavior?: string,
    iteration: number = 1
  ) => {
    const response = await apiClient.post('/ai/repair', {
      circuit: normalizeCircuit(circuit),
      source_code: sourceCode,
      expected_behavior: expectedBehavior,
      iteration,
    });
    return response.data;
  },

  aiOptimize: async (circuit: CircuitSchema, level: number = 2) => {
    const response = await apiClient.post('/ai/optimize', {
      circuit: normalizeCircuit(circuit),
      level,
    });
    return response.data;
  },

  verifyCircuit: async (
    circuit: CircuitSchema,
    referenceCircuit?: CircuitSchema,
    expectedBehavior?: string
  ) => {
    const response = await apiClient.post('/circuits/verify', {
      circuit: normalizeCircuit(circuit),
      reference_circuit: normalizeCircuit(referenceCircuit),
      expected_behavior: expectedBehavior,
    });
    return response.data;
  },
};
