import React from 'react';
import { GatePalette } from './GatePalette';
import { CircuitCanvas } from './CircuitCanvas';
import { CircuitSchema } from '@/lib/apiClient';

interface CircuitBuilderProps {
  circuit: CircuitSchema;
  onChange: (circuit: CircuitSchema) => void;
}

export function CircuitBuilder({ circuit, onChange }: CircuitBuilderProps) {
  const handleAddQubit = () => {
    onChange({
      ...circuit,
      num_qubits: circuit.num_qubits + 1,
      num_clbits: circuit.num_clbits + 1,
    });
  };

  const handleRemoveQubit = () => {
    if (circuit.num_qubits <= 1) return;
    
    // Filter out gates/measurements that touch the removed qubit
    const newQ = circuit.num_qubits - 1;
    const newCircuit = {
      ...circuit,
      num_qubits: newQ,
      num_clbits: newQ,
      gates: circuit.gates.filter(g => !g.qubits.includes(newQ)),
      measurements: circuit.measurements.filter(m => m.qubit !== newQ && m.clbit !== newQ)
    };
    
    onChange(newCircuit);
  };

  return (
    <div className="flex h-full gap-4">
      <div className="w-48 flex-shrink-0">
        <GatePalette />
      </div>
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex justify-between items-center mb-2 px-2">
          <span className="text-sm font-semibold text-gray-300">Circuit Canvas</span>
          <div className="flex gap-2">
            <button 
              onClick={handleRemoveQubit}
              className="px-3 py-1 bg-red-900/50 hover:bg-red-800 text-red-200 text-xs rounded transition-colors"
            >
              - Qubit
            </button>
            <button 
              onClick={handleAddQubit}
              className="px-3 py-1 bg-green-900/50 hover:bg-green-800 text-green-200 text-xs rounded transition-colors"
            >
              + Qubit
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <CircuitCanvas circuit={circuit} onCircuitChange={onChange} />
        </div>
        <div className="mt-2 text-xs text-gray-500 text-center">
          Drag gates from the palette onto the wires. Click a gate or measurement to remove it.
        </div>
      </div>
    </div>
  );
}
