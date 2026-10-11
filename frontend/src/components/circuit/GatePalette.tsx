import React from 'react';

const SUPPORTED_GATES = ['h', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz', 'cx', 'swap'];

export function GatePalette() {
  const handleDragStart = (e: React.DragEvent, gateName: string) => {
    e.dataTransfer.setData('gateName', gateName);
    e.dataTransfer.effectAllowed = 'copy';
  };

  return (
    <div className="flex flex-col h-full bg-gray-800 rounded-lg border border-gray-700">
      <div className="p-3 border-b border-gray-700 bg-gray-800/50">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Gate Palette</h2>
      </div>
      <div className="p-4 grid grid-cols-2 gap-2 overflow-y-auto">
        {SUPPORTED_GATES.map(gate => (
          <div
            key={gate}
            draggable
            onDragStart={(e) => handleDragStart(e, gate)}
            className="bg-blue-900/40 hover:bg-blue-800/60 border border-blue-700 rounded p-2 text-center text-blue-200 font-mono text-sm cursor-grab active:cursor-grabbing select-none transition-colors"
          >
            {gate.toUpperCase()}
          </div>
        ))}
        <div
          draggable
          onDragStart={(e) => handleDragStart(e, 'measure')}
          className="bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded p-2 text-center text-gray-200 font-mono text-sm cursor-grab active:cursor-grabbing select-none transition-colors col-span-2 mt-2"
        >
          MEASURE
        </div>
      </div>
    </div>
  );
}
