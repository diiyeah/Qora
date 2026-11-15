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
    <div className="h-screen bg-background text-textMain flex flex-col font-sans overflow-hidden">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-borders bg-panels flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-6">
          <h1 className="text-lg font-bold text-primary tracking-wide">QORA</h1>
          <div className="flex gap-2">
            <span className="text-sm px-3 py-1 bg-borders rounded text-textMain">🧪 Development Lab</span>
            <span className="text-sm px-3 py-1 hover:bg-borders rounded text-muted cursor-pointer transition-colors">📚 Learning</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Status System */}
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-warning animate-pulse' : 'bg-success'}`}></span>
            <span className={isLoading ? 'text-warning' : 'text-success'}>{isLoading ? 'Running...' : 'Ready'}</span>
          </div>
          
          <button onClick={handleRun} disabled={isLoading} className="btn-primary flex items-center gap-2 text-sm py-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            Run
          </button>
          <button onClick={handleSaveWorkspace} className="btn-secondary text-sm py-1.5">Save</button>
          
          <div className="h-6 w-px bg-borders mx-2"></div>
          
          <select 
            value={selectedBackend} 
            onChange={e => setSelectedBackend(e.target.value)}
            className="bg-background text-sm border border-borders rounded px-2 py-1 outline-none focus:border-primary"
          >
            {backends.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      </header>
      
      {/* 3-Pane Main Content */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Pane: Project / Files (Placeholder) */}
        <div className="w-64 border-r border-borders bg-panels flex flex-col shrink-0">
          <div className="p-3 text-xs font-semibold text-muted uppercase tracking-wider border-b border-borders">
            Workspace
          </div>
          <div className="p-2 space-y-1">
            <div className="px-3 py-1.5 text-sm bg-borders text-textMain rounded cursor-pointer flex items-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
              main_circuit.py
            </div>
          </div>
        </div>
        
        {/* Center Pane: Development (Code + Circuit + Results) */}
        <div className="flex-1 flex flex-col min-w-0 bg-background overflow-y-auto">
          {/* Editor Header */}
          <div className="h-10 border-b border-borders flex items-center px-4 bg-panels shrink-0">
            <div className="flex gap-4">
               <button 
                  className={`text-sm font-medium border-b-2 px-1 py-2 ${activeTab === 'code' ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-textMain'}`}
                  onClick={() => handleTabChange('code')}
                >
                  Code Editor
                </button>
               <button 
                  className={`text-sm font-medium border-b-2 px-1 py-2 ${activeTab === 'builder' ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-textMain'}`}
                  onClick={() => handleTabChange('builder')}
                >
                  Circuit Builder
                </button>
            </div>
          </div>
          
          {/* Main Editing Area */}
          <div className="flex-1 relative min-h-[400px]">
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
          </div>
          
          {/* Results Area (Bottom Split) */}
          <div className="h-1/3 border-t border-borders bg-panels flex flex-col shrink-0 min-h-[300px]">
            <div className="h-10 border-b border-borders flex items-center px-4 shrink-0 bg-background/50">
               <span className="text-sm font-medium text-muted uppercase tracking-wider">Results</span>
               {useNoise && <span className="ml-4 text-xs font-normal bg-warning/20 text-warning px-2 py-0.5 rounded">Noise Active</span>}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <ResultsPanel 
                  circuitSchema={schema}
                  results={results} 
                  isLoading={isLoading} 
                  error={error} 
                />
            </div>
          </div>
        </div>
        
        {/* Right Pane: AI Copilot */}
        <div className="w-80 border-l border-borders bg-panels flex flex-col shrink-0">
          <div className="h-10 border-b border-borders flex items-center px-4 shrink-0">
            <span className="text-sm font-medium text-primary flex items-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
              QORA Copilot
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
             {/* Evidence-based AI Card Placeholder */}
             <div className="panel p-3 border-l-4 border-l-primary">
                <p className="text-sm text-textMain mb-2">✦ I am analyzing your workspace.</p>
                <p className="text-xs text-muted mb-3">Awaiting execution data to provide insights...</p>
                <button className="w-full text-xs py-1.5 bg-background border border-borders rounded text-textMain hover:border-primary transition-colors">
                  Optimize Circuit
                </button>
             </div>
             
             {error && (
                <div className="panel p-3 border-l-4 border-l-error">
                  <p className="text-sm font-medium text-error flex items-center gap-2 mb-2">
                    ⚠ Execution Mismatch
                  </p>
                  <p className="text-xs text-textMain mb-2">Your circuit failed to execute or validate properly.</p>
                  <div className="bg-background rounded p-2 text-xs text-muted mb-3 font-mono">
                    {error}
                  </div>
                  <button className="w-full text-xs py-1.5 bg-background border border-borders rounded text-textMain hover:border-error transition-colors">
                    Diagnose Issue
                  </button>
                </div>
             )}
          </div>
        </div>
        
      </div>
    </div>
  );
}
