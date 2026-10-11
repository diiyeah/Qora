import React from 'react';

export interface BlochSphereProps {
  qubitId: number;
  // A simplified state representation for the mock
  theta: number; // polar angle 0 to PI
  phi: number;   // azimuthal angle 0 to 2PI
  r: number;     // length of the Bloch vector (purity)
}

export function BlochSphere({ qubitId, theta, phi, r }: BlochSphereProps) {
  const isMixed = r < 0.99;
  
  // Calculate projected 2D coordinates for the vector tip
  // 3D coords: x = r * sin(theta) * cos(phi), y = r * sin(theta) * sin(phi), z = r * cos(theta)
  // For 2D SVG, we use a pseudo-isometric projection
  const radius = 50;
  
  // Z axis is up/down, X and Y are diagonal
  const x = Math.sin(theta) * Math.cos(phi) * r;
  const y = Math.sin(theta) * Math.sin(phi) * r;
  const z = Math.cos(theta) * r;
  
  // Map to 2D canvas (center at 60,60)
  const cx = 60 + (x * 0.7 - y * 0.7) * radius;
  const cy = 60 - z * radius + (x * 0.3 + y * 0.3) * radius;

  return (
    <div className="flex flex-col items-center p-2 bg-gray-900 border border-gray-700 rounded-lg">
      <div className="text-sm font-semibold text-gray-300 mb-2">Qubit {qubitId}</div>
      <svg width="120" height="120" className="overflow-visible">
        {/* Sphere wireframe */}
        <circle cx="60" cy="60" r={radius} fill="rgba(30, 58, 138, 0.2)" stroke="#4B5563" strokeWidth="1" />
        <ellipse cx="60" cy="60" rx={radius} ry={radius * 0.3} fill="none" stroke="#4B5563" strokeWidth="1" strokeDasharray="2 2" />
        
        {/* Axes */}
        <line x1="60" y1={60 - radius} x2="60" y2={60 + radius} stroke="#6B7280" strokeWidth="1" />
        <line x1={60 - radius} y1="60" x2={60 + radius} y2="60" stroke="#6B7280" strokeWidth="1" />
        
        {/* State Vector */}
        <line x1="60" y1="60" x2={cx} y2={cy} stroke="#F87171" strokeWidth="3" />
        <circle cx={cx} cy={cy} r="3" fill="#F87171" />
        
        {/* Labels */}
        <text x="60" y={60 - radius - 5} fill="#9CA3AF" fontSize="10" textAnchor="middle">|0⟩</text>
        <text x="60" y={60 + radius + 12} fill="#9CA3AF" fontSize="10" textAnchor="middle">|1⟩</text>
      </svg>
      {isMixed && (
        <div className="mt-2 text-xs text-yellow-400 bg-yellow-900/30 px-2 py-1 rounded">
          Mixed State (Purity: {r.toFixed(2)})
        </div>
      )}
    </div>
  );
}
