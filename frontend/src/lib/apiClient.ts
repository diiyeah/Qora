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
    const response = await apiClient.post('/analyze', { circuit });
    return response.data;
  },
  
  getBackends: async () => {
    const response = await apiClient.get('/backends');
    return response.data;
  }
};
