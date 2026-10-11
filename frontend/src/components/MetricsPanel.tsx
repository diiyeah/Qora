import React from 'react';

export interface MetricsData {
  total_gates: number;
  qubits: number;
  depth: number;
  cnot_count: number;
  gate_types: Record<string, number>;
}

export function MetricsPanel({ metrics }: { metrics: MetricsData | null }) {
  if (!metrics) return null;

  return (
    <div className="mb-6 bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wider">Circuit Metrics</h3>
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="bg-gray-800 p-3 rounded text-center">
          <div className="text-2xl font-bold text-blue-400">{metrics.qubits}</div>
          <div className="text-xs text-gray-500 uppercase">Qubits</div>
        </div>
        <div className="bg-gray-800 p-3 rounded text-center">
          <div className="text-2xl font-bold text-blue-400">{metrics.depth}</div>
          <div className="text-xs text-gray-500 uppercase">Depth</div>
        </div>
        <div className="bg-gray-800 p-3 rounded text-center">
          <div className="text-2xl font-bold text-purple-400">{metrics.total_gates}</div>
          <div className="text-xs text-gray-500 uppercase">Total Gates</div>
        </div>
        <div className="bg-gray-800 p-3 rounded text-center">
          <div className="text-2xl font-bold text-purple-400">{metrics.cnot_count}</div>
          <div className="text-xs text-gray-500 uppercase">CNOTs</div>
        </div>
      </div>
      
      <div>
        <h4 className="text-xs text-gray-400 mb-2">Gate Breakdown</h4>
        <div className="flex gap-2 flex-wrap">
          {Object.entries(metrics.gate_types).map(([gate, count]) => (
            <div key={gate} className="bg-gray-800 px-3 py-1 rounded text-sm text-gray-300">
              <span className="font-mono text-blue-300 mr-2">{gate.toUpperCase()}</span>
              {count}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
