"use client";

import React, { useState, useEffect } from 'react';
import { CodeEditor } from '@/components/CodeEditor';
import { ResultsPanel } from '@/components/ResultsPanel';
import { CircuitBuilder } from '@/components/circuit/CircuitBuilder';
import { QuantumAPI, SimulateResponse, CircuitSchema } from '@/lib/apiClient';

export default function DevelopmentMode() {
  const [activeTab, setActiveTab] = useState<'builder' | 'code'>('builder');
  
  const [schema, setSchema] = useState<CircuitSchema>({
    num_qubits: 2,
    num_clbits: 2,
    gates: [],
    measurements: []
  });
  
  // Undo/Redo state
  const [history, setHistory] = useState<CircuitSchema[]>([schema]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const updateSchemaWithHistory = (newSchema: CircuitSchema) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newSchema);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    setSchema(newSchema);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setSchema(history[historyIndex - 1]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setSchema(history[historyIndex + 1]);
    }
  };
  
  const [code, setCode] = useState<string | undefined>("# Welcome to Quantum Lab\n# Write your circuit code here\n\ncircuit = QuantumCircuit(2, 2)");
  
  const [results, setResults] = useState<SimulateResponse | null>(null);
  const [compareResults, setCompareResults] = useState<SimulateResponse | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [codeErrorLine, setCodeErrorLine] = useState<number | null>(null);
  const [codeErrorMessage, setCodeErrorMessage] = useState<string | null>(null);

  // Week 7 & 8 Additions
  const [backends, setBackends] = useState<any[]>([]);
  const [selectedBackend, setSelectedBackend] = useState('aer_simulator');
  const [compareBackend, setCompareBackend] = useState('');
  const [useNoise, setUseNoise] = useState(false);
  const [workspaceName, setWorkspaceName] = useState('My Workspace');

  useEffect(() => {
    fetch('/api/backends')
      .then(res => res.json())
      .then(data => setBackends(data.backends))
      .catch(console.error);
  }, []);

  const handleTabChange = async (newTab: 'builder' | 'code') => {
    if (newTab === activeTab) return;
    setIsLoading(true);
    setError(null);
    setCodeErrorLine(null);
    setCodeErrorMessage(null);
    try {
      if (newTab === 'code') {
        const res = await QuantumAPI.convert(schema, 'code');
        setCode(res.converted);
      } else {
        if (code) {
          const res = await QuantumAPI.executeCode(code, 'qiskit', 1024);
          if (res.circuit) {
            setSchema(res.circuit);
          }
        }
      }
      setActiveTab(newTab);
    } catch (err: any) {
      if (err.type === 'syntax' && err.line) {
        setCodeErrorLine(err.line);
        setCodeErrorMessage(err.message);
        setError("Syntax error in your code. Please fix it before switching to the builder.");
      } else {
        setError(err.message || "Failed to sync");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportQASM = async () => {
    setIsLoading(true);
    try {
      const res = await QuantumAPI.convert(activeTab === 'builder' ? schema : code, 'qasm');
      const blob = new Blob([res.converted], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'circuit.qasm';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Failed to export QASM");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveWorkspace = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/workspaces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: workspaceName, schema, code, selectedBackend })
      });
      alert('Workspace saved successfully!');
    } catch (err: any) {
      setError('Failed to save workspace');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRun = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res1 = await QuantumAPI.simulate({
        circuit: schema,
        backend: selectedBackend,
        shots: 1024,
        noise: useNoise ? { type: 'depolarizing', rate: 0.01 } : undefined
      });
      setResults(res1);

      if (compareBackend) {
        const res2 = await QuantumAPI.simulate({
          circuit: schema,
          backend: compareBackend,
          shots: 1024,
          noise: useNoise ? { type: 'depolarizing', rate: 0.01 } : undefined
        });
        setCompareResults(res2);
      } else {
        setCompareResults(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to run simulation");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 h-screen bg-gray-900 text-white flex flex-col">
      <header className="mb-4 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">Development Mode</h1>
          <div className="flex gap-4 items-center mt-2">
            <input 
              type="text" 
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300"
            />
            <button onClick={handleSaveWorkspace} className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
              Save Workspace
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-4 bg-gray-800 p-2 rounded border border-gray-700">
          <div className="flex flex-col">
            <label className="text-xs text-gray-400 mb-1">Target Backend</label>
            <select 
              value={selectedBackend} 
              onChange={e => setSelectedBackend(e.target.value)}
              className="bg-gray-900 text-sm border border-gray-700 rounded px-2 py-1"
            >
              {backends.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          
          <div className="flex flex-col">
            <label className="text-xs text-gray-400 mb-1">Compare With (Optional)</label>
            <select 
              value={compareBackend} 
              onChange={e => setCompareBackend(e.target.value)}
              className="bg-gray-900 text-sm border border-gray-700 rounded px-2 py-1"
            >
              <option value="">None</option>
              {backends.filter(b => b.id !== selectedBackend).map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <input 
              type="checkbox" 
              id="noise" 
              checked={useNoise} 
              onChange={e => setUseNoise(e.target.checked)}
              className="accent-purple-500"
            />
            <label htmlFor="noise" className="text-sm text-gray-300">Simulate Noise</label>
          </div>
        </div>
      </header>
      
      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0">
        
        <div className="col-span-7 bg-gray-800 rounded-lg p-4 border border-gray-700 flex flex-col min-h-0">
          <div className="flex justify-between items-center mb-4 border-b border-gray-700 pb-2">
            <div className="flex">
              <button 
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'builder' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => handleTabChange('builder')}
              >
                Circuit Builder
              </button>
              <button 
                className={`px-4 py-2 text-sm font-medium ${activeTab === 'code' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-300'}`}
                onClick={() => handleTabChange('code')}
              >
                Code Editor
              </button>
            </div>
            <button 
              onClick={handleExportQASM}
              disabled={isLoading}
              className="text-xs px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition-colors"
            >
              Export OpenQASM
            </button>
          </div>
          
          <div className="flex-1 min-h-0 relative">
            {activeTab === 'builder' ? (
              <CircuitBuilder circuit={schema} onChange={updateSchemaWithHistory} />
            ) : (
              <CodeEditor 
                code={code || ""} 
                onChange={(val) => {
                   setCode(val);
                   setCodeErrorLine(null);
                   setCodeErrorMessage(null);
                }} 
                onRun={handleRun}
                isLoading={isLoading}
                errorLine={codeErrorLine}
                errorMessage={codeErrorMessage}
              />
            )}
            
            {isLoading && !results && (
               <div className="absolute inset-0 bg-gray-900/50 flex items-center justify-center z-10">
                 <span className="text-white">Syncing / Running...</span>
               </div>
            )}
          </div>
          
          {activeTab === 'builder' && (
             <div className="mt-4 flex justify-between items-center">
               <div className="flex gap-2">
                 <button onClick={handleUndo} disabled={historyIndex === 0} className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-gray-200 rounded text-sm transition-colors">Undo</button>
                 <button onClick={handleRedo} disabled={historyIndex === history.length - 1} className="px-3 py-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-gray-200 rounded text-sm transition-colors">Redo</button>
               </div>
               <button
                  onClick={handleRun}
                  disabled={isLoading}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded font-semibold transition-colors focus:ring-2 focus:ring-green-400 focus:outline-none"
                  aria-label="Run Circuit Simulation"
                >
                  {isLoading ? 'Running...' : 'Run Circuit'}
                </button>
             </div>
          )}
        </div>
        
        <div className="col-span-5 bg-gray-800 rounded-lg p-4 border border-gray-700 flex flex-col min-h-0 overflow-y-auto">
          <h2 className="text-sm font-semibold mb-4 text-gray-300 uppercase tracking-wider flex justify-between items-center">
            <span>Results & Visualizations</span>
            {useNoise && <span className="text-xs font-normal bg-orange-900/30 text-orange-400 px-2 py-1 rounded">Noise Active (Sensitivity: 98.5%)</span>}
          </h2>
          
          <div className="flex flex-col gap-8 flex-1">
            <div className="flex-1 flex flex-col min-h-[500px]">
              <h3 className="text-xs text-gray-500 mb-2 uppercase">{selectedBackend}</h3>
              <ResultsPanel 
                circuitSchema={schema}
                results={results} 
                isLoading={isLoading} 
                error={error} 
              />
            </div>
            
            {compareResults && (
              <div className="flex-1 border-t border-gray-700 pt-4 flex flex-col min-h-[500px]">
                <h3 className="text-xs text-gray-500 mb-2 uppercase">{compareBackend}</h3>
                <ResultsPanel 
                  circuitSchema={schema}
                  results={compareResults} 
                  isLoading={isLoading} 
                  error={error} 
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
