import React, { useState } from 'react';
import { CircuitSchema } from '@/lib/apiClient';

interface CircuitCanvasProps {
  circuit: CircuitSchema;
  onCircuitChange: (newCircuit: CircuitSchema) => void;
}

const LAYER_WIDTH = 60;
const QUBIT_HEIGHT = 60;
const PADDING = 40;

export function CircuitCanvas({ circuit, onCircuitChange }: CircuitCanvasProps) {
  const [dragHover, setDragHover] = useState<{ layer: number; qubit: number } | null>(null);

  const numLayers = Math.max(
    8,
    ...circuit.gates.map((g) => g.layer || 0),
    ...circuit.measurements.map((m) => circuit.gates.length + 1)
  ) + 2;

  const handleDragOver = (e: React.DragEvent, layer: number, qubit: number) => {
    e.preventDefault();
    setDragHover({ layer, qubit });
  };

  const handleDragLeave = () => {
    setDragHover(null);
  };

  const handleDrop = (e: React.DragEvent, layer: number, qubit: number) => {
    e.preventDefault();
    setDragHover(null);
    
    const gateName = e.dataTransfer.getData('gateName');
    if (!gateName) return;

    if (gateName === 'measure') {
      const newCircuit = { ...circuit };
      // Remove existing measurement for this qubit if any
      newCircuit.measurements = newCircuit.measurements.filter(m => m.qubit !== qubit);
      newCircuit.measurements.push({ qubit, clbit: qubit });
      onCircuitChange(newCircuit);
      return;
    }

    const newCircuit = { ...circuit };
    // Very simple check: remove gate if it exists at this position
    newCircuit.gates = newCircuit.gates.filter(
      (g) => !(g.layer === layer && g.qubits.includes(qubit))
    );

    // Prompt for params if it's a rotation gate
    let params: number[] = [];
    if (['rx', 'ry', 'rz'].includes(gateName)) {
      const angle = window.prompt(`Enter angle for ${gateName.toUpperCase()} gate (e.g. 1.57):`, '1.57');
      if (angle === null) return; // User cancelled
      params = [parseFloat(angle) || 0];
    }

    let qubits = [qubit];
    if (gateName === 'cx' || gateName === 'swap') {
      const target = window.prompt(`Enter target qubit for ${gateName.toUpperCase()} (control is ${qubit}):`, ((qubit + 1) % circuit.num_qubits).toString());
      if (target === null) return;
      const t = parseInt(target);
      if (t >= 0 && t < circuit.num_qubits && t !== qubit) {
        qubits = [qubit, t];
      } else {
        alert("Invalid target qubit");
        return;
      }
    }

    newCircuit.gates.push({
      name: gateName,
      qubits: qubits,
      layer: layer,
      ...(params.length > 0 ? { params } : {})
    });
    
    onCircuitChange(newCircuit);
  };

  const handleGateClick = (gateIndex: number) => {
    if (window.confirm("Delete this gate?")) {
      const newCircuit = { ...circuit };
      newCircuit.gates.splice(gateIndex, 1);
      onCircuitChange(newCircuit);
    }
  };

  const handleMeasurementClick = (mIndex: number) => {
    if (window.confirm("Delete this measurement?")) {
      const newCircuit = { ...circuit };
      newCircuit.measurements.splice(mIndex, 1);
      onCircuitChange(newCircuit);
    }
  };

  const svgWidth = PADDING * 2 + numLayers * LAYER_WIDTH;
  const svgHeight = PADDING * 2 + Math.max(circuit.num_qubits, circuit.num_clbits) * QUBIT_HEIGHT;

  return (
    <div className="w-full h-full overflow-auto bg-gray-900 border border-gray-700 rounded-lg relative" role="region" aria-label="Circuit Canvas">
      <svg width={svgWidth} height={svgHeight} className="min-w-full min-h-full" role="img" aria-label="Interactive Quantum Circuit Schema">
        {/* Wires */}
        {Array.from({ length: circuit.num_qubits }).map((_, qIdx) => {
          const y = PADDING + qIdx * QUBIT_HEIGHT;
          return (
            <g key={`wire-q-${qIdx}`}>
              <line x1={PADDING} y1={y} x2={svgWidth - PADDING} y2={y} stroke="#4B5563" strokeWidth="2" />
              <text x={PADDING - 10} y={y + 5} fill="#9CA3AF" fontSize="14" textAnchor="end" fontFamily="monospace" aria-hidden="true">
                q[{qIdx}]
              </text>
            </g>
          );
        })}
        {Array.from({ length: circuit.num_clbits }).map((_, cIdx) => {
          const y = PADDING + circuit.num_qubits * QUBIT_HEIGHT + cIdx * QUBIT_HEIGHT;
          return (
            <g key={`wire-c-${cIdx}`}>
              <line x1={PADDING} y1={y - 2} x2={svgWidth - PADDING} y2={y - 2} stroke="#6B7280" strokeWidth="1" />
              <line x1={PADDING} y1={y + 2} x2={svgWidth - PADDING} y2={y + 2} stroke="#6B7280" strokeWidth="1" />
              <text x={PADDING - 10} y={y + 5} fill="#9CA3AF" fontSize="14" textAnchor="end" fontFamily="monospace" aria-hidden="true">
                c[{cIdx}]
              </text>
            </g>
          );
        })}

        {/* Drop zones for grid mapping */}
        {Array.from({ length: circuit.num_qubits }).map((_, qIdx) => (
          Array.from({ length: numLayers }).map((_, lIdx) => {
            const cx = PADDING + lIdx * LAYER_WIDTH + LAYER_WIDTH / 2;
            const cy = PADDING + qIdx * QUBIT_HEIGHT;
            const isHover = dragHover?.layer === lIdx && dragHover?.qubit === qIdx;
            
            return (
              <rect
                key={`drop-${qIdx}-${lIdx}`}
                x={cx - LAYER_WIDTH / 2}
                y={cy - QUBIT_HEIGHT / 2}
                width={LAYER_WIDTH}
                height={QUBIT_HEIGHT}
                fill={isHover ? "rgba(59, 130, 246, 0.2)" : "transparent"}
                onDragOver={(e) => handleDragOver(e, lIdx, qIdx)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, lIdx, qIdx)}
                role="button"
                aria-label={`Drop zone at layer ${lIdx}, qubit ${qIdx}`}
                tabIndex={0}
              />
            );
          })
        ))}

        {/* Gates */}
        {circuit.gates.map((gate, idx) => {
          const cx = PADDING + (gate.layer || 0) * LAYER_WIDTH + LAYER_WIDTH / 2;
          const qMain = gate.qubits[0];
          const cy = PADDING + qMain * QUBIT_HEIGHT;
          
          let gateVisual = null;
          
          if (gate.name === 'cx') {
            const targetQ = gate.qubits[1];
            const tCy = PADDING + targetQ * QUBIT_HEIGHT;
            gateVisual = (
              <g 
                onClick={() => handleGateClick(idx)} 
                className="cursor-pointer"
                role="button"
                aria-label={`CX gate connecting qubit ${qMain} and target ${targetQ}`}
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleGateClick(idx)}
              >
                <line x1={cx} y1={cy} x2={cx} y2={tCy} stroke="#60A5FA" strokeWidth="2" />
                <circle cx={cx} cy={cy} r="6" fill="#60A5FA" />
                <circle cx={cx} cy={tCy} r="12" fill="#1E3A8A" stroke="#60A5FA" strokeWidth="2" />
                <line x1={cx - 8} y1={tCy} x2={cx + 8} y2={tCy} stroke="#60A5FA" strokeWidth="2" />
                <line x1={cx} y1={tCy - 8} x2={cx} y2={tCy + 8} stroke="#60A5FA" strokeWidth="2" />
              </g>
            );
          } else {
            gateVisual = (
              <g 
                onClick={() => handleGateClick(idx)} 
                className="cursor-pointer"
                role="button"
                aria-label={`${gate.name.toUpperCase()} gate on qubit ${qMain}`}
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleGateClick(idx)}
              >
                <rect x={cx - 20} y={cy - 20} width="40" height="40" fill="#1E3A8A" stroke="#60A5FA" strokeWidth="2" rx="4" />
                <text x={cx} y={cy + 5} fill="white" fontSize="16" textAnchor="middle" fontFamily="monospace" aria-hidden="true">
                  {gate.name.toUpperCase()}
                </text>
                {gate.params && (
                  <text x={cx} y={cy + 30} fill="#9CA3AF" fontSize="10" textAnchor="middle" aria-hidden="true">
                    ({gate.params.map(p => p.toFixed(2)).join(',')})
                  </text>
                )}
              </g>
            );
          }
          
          return <g key={`gate-${idx}`}>{gateVisual}</g>;
        })}

        {/* Measurements */}
        {circuit.measurements.map((m, idx) => {
          const lIdx = numLayers - 2; // Arbitrary placing at the end for simplicity
          const cx = PADDING + lIdx * LAYER_WIDTH + LAYER_WIDTH / 2;
          const cyQ = PADDING + m.qubit * QUBIT_HEIGHT;
          const cyC = PADDING + circuit.num_qubits * QUBIT_HEIGHT + m.clbit * QUBIT_HEIGHT;
          
          return (
            <g 
              key={`meas-${idx}`} 
              onClick={() => handleMeasurementClick(idx)} 
              className="cursor-pointer"
              role="button"
              aria-label={`Measurement on qubit ${m.qubit} to classical bit ${m.clbit}`}
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleMeasurementClick(idx)}
            >
              <line x1={cx} y1={cyQ} x2={cx} y2={cyC} stroke="#9CA3AF" strokeWidth="2" strokeDasharray="4 4" />
              <rect x={cx - 15} y={cyQ - 15} width="30" height="30" fill="#374151" stroke="#9CA3AF" strokeWidth="2" rx="2" />
              <path d={`M ${cx - 10} ${cyQ + 5} Q ${cx} ${cyQ - 10} ${cx + 10} ${cyQ + 5}`} fill="none" stroke="#9CA3AF" strokeWidth="2" />
              <line x1={cx} y1={cyQ + 5} x2={cx + 5} y2={cyQ - 5} stroke="#9CA3AF" strokeWidth="2" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
