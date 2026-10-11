import React, { useState, useEffect } from 'react';
import { Histogram } from './Charts';
import { MetricsPanel, MetricsData } from './MetricsPanel';
import { BlochSphere } from './BlochSphere';
import type { SimulateResponse } from '../lib/apiClient';
import { QuantumAPI } from '../lib/apiClient';

interface ResultsPanelProps {
  circuitSchema?: any; // To fetch metrics
  results: SimulateResponse | null;
  isLoading: boolean;
  error: string | null;
}

export function ResultsPanel({ circuitSchema, results, isLoading, error }: ResultsPanelProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [evolutionStep, setEvolutionStep] = useState(0);

  useEffect(() => {
    if (circuitSchema && results) {
      QuantumAPI.analyze(circuitSchema).then(res => setMetrics(res.metrics)).catch(console.error);
    }
  }, [circuitSchema, results]);

  useEffect(() => {
    if (results?.per_gate_states) {
      setEvolutionStep(results.per_gate_states.length - 1);
    }
  }, [results]);
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <p>Running simulation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-4 text-red-400 bg-red-900/20 rounded">
        <p className="font-semibold mb-2">Simulation Error</p>
        <pre className="text-sm overflow-auto">{error}</pre>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <p>Run the circuit to see results</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto pr-2">
      <MetricsPanel metrics={metrics} />
      
      {results.per_gate_states && results.per_gate_states.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wider">Gate-by-Gate Evolution</h3>
          
          <div className="flex gap-4 overflow-x-auto pb-4">
            {results.per_gate_states[evolutionStep].map((qState: any, idx: number) => (
              <BlochSphere 
                key={idx} 
                qubitId={idx} 
                theta={qState.theta} 
                phi={qState.phi} 
                r={qState.r} 
              />
            ))}
          </div>
          
          <div className="flex items-center gap-4 mt-2 bg-gray-900 p-3 rounded-lg border border-gray-700">
            <span className="text-sm text-gray-400">Step {evolutionStep}</span>
            <input 
              type="range" 
              min="0" 
              max={results.per_gate_states.length - 1} 
              value={evolutionStep}
              onChange={(e) => setEvolutionStep(parseInt(e.target.value))}
              className="flex-1 accent-blue-500 cursor-pointer"
            />
            <span className="text-sm text-gray-400">Max {results.per_gate_states.length - 1}</span>
          </div>
        </div>
      )}

      <Histogram 
        title={`Measurement Counts (Shots: ${results.backend_info.shots})`}
        data={results.counts} 
        fillColor="#3B82F6" 
      />
      
      <Histogram 
        title="Probabilities"
        data={results.probabilities} 
        fillColor="#8B5CF6" 
      />
      
      <div className="mt-6">
        <h3 className="text-sm text-gray-400 mb-2">Statevector (Final)</h3>
        <div className="bg-gray-900 p-3 rounded overflow-x-auto border border-gray-700">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="pb-2">State</th>
                <th className="pb-2">Real</th>
                <th className="pb-2">Imaginary</th>
              </tr>
            </thead>
            <tbody>
              {results.statevector.map((amp, idx) => {
                const stateStr = idx.toString(2).padStart(Math.log2(results.statevector.length), '0');
                if (Math.abs(amp[0]) < 1e-10 && Math.abs(amp[1]) < 1e-10) return null; // Skip near-zero states
                return (
                  <tr key={idx} className="border-b border-gray-800 last:border-0">
                    <td className="py-2 font-mono text-blue-400">|{stateStr}⟩</td>
                    <td className="py-2">{amp[0].toFixed(4)}</td>
                    <td className="py-2">{amp[1].toFixed(4)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
