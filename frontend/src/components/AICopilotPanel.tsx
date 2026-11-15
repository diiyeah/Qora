"use client";

import React, { useState } from 'react';
import { CircuitSchema, QuantumAPI } from '@/lib/apiClient';

interface AICopilotPanelProps {
  currentCircuit: CircuitSchema;
  currentCode?: string;
  onApplyCircuit: (circuit: CircuitSchema) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  evidence?: {
    qubit_count: number;
    depth: number;
    gate_count: number;
    cnot_count: number;
    measurement_distribution: Record<string, number>;
  };
}

export const AICopilotPanel: React.FC<AICopilotPanelProps> = ({
  currentCircuit,
  currentCode,
  onApplyCircuit,
}) => {
  const [activeTab, setActiveTab] = useState<'generate' | 'chat' | 'diagnose' | 'repair' | 'optimize'>('generate');

  // Generation state
  const [generatePrompt, setGeneratePrompt] = useState('Create a two-qubit Bell state');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<any | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text: 'Hello! I am QORA Copilot. I reason directly over real quantum circuits, simulation counts, and metrics.',
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Diagnosis state
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState<any | null>(null);
  const [diagError, setDiagError] = useState<string | null>(null);

  // Repair state
  const [isRepairing, setIsRepairing] = useState(false);
  const [repairProposal, setRepairProposal] = useState<any | null>(null);
  const [repairIteration, setRepairIteration] = useState(1);
  const [repairError, setRepairError] = useState<string | null>(null);
  const [repairBanner, setRepairBanner] = useState<string | null>(null);

  // Optimization state
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optLevel, setOptLevel] = useState<number>(2);
  const [optimizationResult, setOptimizationResult] = useState<any | null>(null);
  const [optError, setOptError] = useState<string | null>(null);
  const [optBanner, setOptBanner] = useState<string | null>(null);

  const handleOptimize = async (level: number = optLevel) => {
    setIsOptimizing(true);
    setOptError(null);
    setOptBanner(null);
    try {
      const res = await QuantumAPI.aiOptimize(currentCircuit, level);
      setOptimizationResult(res);
      if (res.transformations && res.transformations.length > 0) {
        setOptBanner(`Optimization found ${res.transformations.length} simplification opportunity(ies).`);
      } else {
        setOptBanner('Circuit is already in optimal canonical form.');
      }
    } catch (err: any) {
      setOptError(err.message || 'Circuit optimization failed.');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApplyOptimization = () => {
    if (optimizationResult?.optimized_circuit) {
      onApplyCircuit(optimizationResult.optimized_circuit);
      setOptBanner('Optimized circuit applied to workspace!');
    }
  };

  const handleRejectOptimization = () => {
    setOptimizationResult(null);
    setOptBanner('Optimization rejected. Kept original circuit.');
  };

  const handleGenerate = async (promptToUse?: string) => {
    const prompt = promptToUse || generatePrompt;
    if (!prompt.trim()) return;
    setIsGenerating(true);
    setGenError(null);
    try {
      const res = await QuantumAPI.aiGenerate(prompt);
      setGeneratedResult(res);
    } catch (err: any) {
      setGenError(err.message || 'Circuit generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userText = chatInput;
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', text: userText }]);
    setIsChatLoading(true);

    try {
      const res = await QuantumAPI.aiChat(userText, currentCircuit);
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: res.response,
          evidence: res.evidence,
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error: ${err.message || 'Unable to process query.'}` },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleRunDiagnosis = async () => {
    setIsDiagnosing(true);
    setDiagError(null);
    try {
      const res = await QuantumAPI.aiDiagnose(currentCircuit, currentCode);
      setDiagnosisResult(res.diagnosis);
    } catch (err: any) {
      setDiagError(err.message || 'Diagnosis failed.');
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleProposeRepair = async (iterationNum: number = 1) => {
    setIsRepairing(true);
    setRepairError(null);
    setRepairBanner(null);
    try {
      const res = await QuantumAPI.aiRepair(currentCircuit, currentCode, undefined, iterationNum);
      setRepairProposal(res.proposal);
      setRepairIteration(res.iteration);
    } catch (err: any) {
      setRepairError(err.message || 'Repair proposal generation failed.');
    } finally {
      setIsRepairing(false);
    }
  };

  const handleApplyRepair = () => {
    if (!repairProposal?.repaired_circuit) return;
    onApplyCircuit(repairProposal.repaired_circuit);
    setRepairBanner('✓ Repaired circuit applied to workspace successfully!');
  };

  const handleRejectRepair = () => {
    setRepairProposal(null);
    setRepairBanner('Repair proposal rejected.');
  };

  return (
    <div className="flex flex-col h-full bg-panels text-textMain">
      {/* Sub-tab Navigation */}
      <div className="flex border-b border-borders text-[11px] font-medium">
        <button
          onClick={() => setActiveTab('generate')}
          className={`flex-1 py-2 text-center transition-colors ${
            activeTab === 'generate'
              ? 'border-b-2 border-primary text-primary font-bold bg-background/40'
              : 'text-muted hover:text-textMain'
          }`}
        >
          ⚡ Generator
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex-1 py-2 text-center transition-colors ${
            activeTab === 'chat'
              ? 'border-b-2 border-primary text-primary font-bold bg-background/40'
              : 'text-muted hover:text-textMain'
          }`}
        >
          💬 Chat
        </button>
        <button
          onClick={() => setActiveTab('diagnose')}
          className={`flex-1 py-2 text-center transition-colors ${
            activeTab === 'diagnose'
              ? 'border-b-2 border-primary text-primary font-bold bg-background/40'
              : 'text-muted hover:text-textMain'
          }`}
        >
          🔍 Diagnosis
        </button>
        <button
          onClick={() => {
            setActiveTab('repair');
            if (!repairProposal && !isRepairing) {
              handleProposeRepair(1);
            }
          }}
          className={`flex-1 py-2 text-center transition-colors ${
            activeTab === 'repair'
              ? 'border-b-2 border-primary text-primary font-bold bg-background/40'
              : 'text-muted hover:text-textMain'
          }`}
        >
          🔧 Repair
        </button>
        <button
          onClick={() => {
            setActiveTab('optimize');
            if (!optimizationResult && !isOptimizing) {
              handleOptimize();
            }
          }}
          className={`flex-1 py-2 text-center transition-colors ${
            activeTab === 'optimize'
              ? 'border-b-2 border-primary text-primary font-bold bg-background/40'
              : 'text-muted hover:text-textMain'
          }`}
        >
          🚀 Optimize
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* TAB 1: NL GENERATOR */}
        {activeTab === 'generate' && (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-muted mb-1">
                Natural-Language Circuit Request
              </label>
              <textarea
                value={generatePrompt}
                onChange={(e) => setGeneratePrompt(e.target.value)}
                placeholder="e.g. Create a two-qubit Bell state |Φ+⟩"
                className="w-full h-20 p-2 text-xs bg-background border border-borders rounded focus:border-primary outline-none resize-none"
              />
            </div>

            {/* Quick Templates */}
            <div className="flex flex-wrap gap-1">
              {[
                'Create a two-qubit Bell state',
                '3-qubit GHZ state',
                'Superposition on 3 qubits',
                'Quantum swap circuit',
              ].map((template) => (
                <button
                  key={template}
                  onClick={() => {
                    setGeneratePrompt(template);
                    handleGenerate(template);
                  }}
                  className="text-[10px] px-2 py-0.5 bg-background border border-borders rounded hover:border-primary transition-colors text-muted hover:text-textMain"
                >
                  {template}
                </button>
              ))}
            </div>

            <button
              onClick={() => handleGenerate()}
              disabled={isGenerating || !generatePrompt.trim()}
              className="w-full py-2 bg-primary text-white text-xs font-semibold rounded hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Synthesizing & Simulating...
                </>
              ) : (
                '🚀 Generate Circuit'
              )}
            </button>

            {genError && (
              <div className="p-2 text-xs bg-error/10 border border-error/30 text-error rounded">
                {genError}
              </div>
            )}

            {generatedResult && (
              <div className="p-3 bg-background border border-borders rounded space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-primary">Generated Result</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] ${
                      generatedResult.validation_passed
                        ? 'bg-success/20 text-success'
                        : 'bg-warning/20 text-warning'
                    }`}
                  >
                    {generatedResult.validation_passed ? 'Verified ✓' : 'Unverified ⚠'}
                  </span>
                </div>

                <p className="text-textMain text-[11px] leading-relaxed">
                  {generatedResult.explanation}
                </p>

                {/* Metrics Pill Grid */}
                <div className="grid grid-cols-3 gap-1 text-[10px] text-center">
                  <div className="p-1 bg-panels rounded border border-borders">
                    <span className="text-muted block">Qubits</span>
                    <span className="font-bold">{generatedResult.circuit.num_qubits}</span>
                  </div>
                  <div className="p-1 bg-panels rounded border border-borders">
                    <span className="text-muted block">Gates</span>
                    <span className="font-bold">{generatedResult.circuit.gates.length}</span>
                  </div>
                  <div className="p-1 bg-panels rounded border border-borders">
                    <span className="text-muted block">Depth</span>
                    <span className="font-bold">{generatedResult.evidence.depth}</span>
                  </div>
                </div>

                {/* Probabilities Preview */}
                {generatedResult.distribution && (
                  <div>
                    <span className="text-muted text-[10px] block mb-1">
                      Aer Measurement Distribution:
                    </span>
                    <div className="flex gap-2">
                      {Object.entries(generatedResult.distribution).map(([state, prob]: any) => (
                        <div
                          key={state}
                          className="flex-1 text-center bg-panels p-1 rounded border border-borders text-[10px]"
                        >
                          <span className="font-mono text-primary font-bold">|{state}⟩</span>:{' '}
                          {(prob * 100).toFixed(1)}%
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => onApplyCircuit(generatedResult.circuit)}
                  className="w-full mt-2 py-1.5 bg-success text-white text-xs font-semibold rounded hover:bg-success/90 transition-colors"
                >
                  📥 Apply Circuit to Workspace
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: COPILOT CHAT */}
        {activeTab === 'chat' && (
          <div className="flex flex-col h-full space-y-3">
            <div className="flex-1 space-y-2 overflow-y-auto max-h-[380px] pr-1">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-2 rounded text-xs ${
                    msg.role === 'user'
                      ? 'bg-primary/10 border border-primary/30 ml-4'
                      : 'bg-background border border-borders mr-2'
                  }`}
                >
                  <span className="block font-semibold text-[10px] text-muted mb-1">
                    {msg.role === 'user' ? 'You' : 'QORA Copilot'}
                  </span>
                  <p className="whitespace-pre-line text-[11px] leading-relaxed">{msg.text}</p>

                  {/* Supporting Evidence Card */}
                  {msg.evidence && (
                    <div className="mt-2 pt-2 border-t border-borders text-[10px] text-muted space-y-1">
                      <div className="font-semibold text-textMain">Verified Execution Evidence:</div>
                      <div>
                        Qubits: {msg.evidence.qubit_count} | Depth: {msg.evidence.depth} | CNOTs:{' '}
                        {msg.evidence.cnot_count}
                      </div>
                      {Object.keys(msg.evidence.measurement_distribution).length > 0 && (
                        <div className="font-mono text-[9px]">
                          Dist:{' '}
                          {Object.entries(msg.evidence.measurement_distribution)
                            .map(([k, v]) => `|${k}⟩: ${(v * 100).toFixed(0)}%`)
                            .join(', ')}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {isChatLoading && (
                <div className="p-2 bg-background border border-borders rounded text-xs text-muted flex items-center gap-2">
                  <span className="w-2.5 h-2.5 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  Reasoning over circuit structure...
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="flex gap-1 pt-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about this circuit or quantum gates..."
                className="flex-1 px-2 py-1.5 text-xs bg-background border border-borders rounded focus:border-primary outline-none"
              />
              <button
                type="submit"
                disabled={isChatLoading || !chatInput.trim()}
                className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </div>
        )}

        {/* TAB 3: DIAGNOSIS */}
        {activeTab === 'diagnose' && (
          <div className="space-y-3">
            <p className="text-xs text-muted leading-relaxed">
              Detect quantum bugs across 9 categories (syntax, qubit mapping, gate ordering,
              measurement, parameters, algorithmic discrepancies).
            </p>

            <button
              onClick={handleRunDiagnosis}
              disabled={isDiagnosing}
              className="w-full py-2 bg-background border border-borders text-textMain text-xs font-semibold rounded hover:border-primary transition-colors flex items-center justify-center gap-2"
            >
              {isDiagnosing ? (
                <>
                  <span className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  Analyzing Circuit Errors...
                </>
              ) : (
                '🔍 Diagnose Active Circuit'
              )}
            </button>

            {diagError && (
              <div className="p-2 text-xs bg-error/10 border border-error/30 text-error rounded">
                {diagError}
              </div>
            )}

            {diagnosisResult && (
              <div className="p-3 bg-background border border-borders rounded space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-warning/20 text-warning">
                    {diagnosisResult.category.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] text-muted">
                    Confidence: {(diagnosisResult.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="font-semibold text-textMain">{diagnosisResult.description}</div>

                <p className="text-[11px] text-muted leading-relaxed">
                  {diagnosisResult.explanation}
                </p>

                {diagnosisResult.suggested_fix && (
                  <div className="p-2 bg-panels border-l-2 border-primary rounded text-[11px] space-y-1">
                    <span className="font-semibold text-primary block">Suggested Fix:</span>
                    <span>{diagnosisResult.suggested_fix}</span>
                  </div>
                )}

                <button
                  onClick={() => {
                    setActiveTab('repair');
                    handleProposeRepair(1);
                  }}
                  className="w-full mt-2 py-1.5 bg-primary text-white text-xs font-semibold rounded hover:bg-primary/90 transition-colors"
                >
                  ⚡ Propose Repair & Preview Diff →
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: REPAIR PROPOSAL & PREVIEW UI (Milestone 4) */}
        {activeTab === 'repair' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-textMain">Repair Proposal & Diff</span>
              <span className="text-[10px] px-2 py-0.5 bg-background border border-borders rounded text-muted">
                Iteration {repairIteration} / 3
              </span>
            </div>

            <button
              onClick={() => handleProposeRepair(repairIteration)}
              disabled={isRepairing}
              className="w-full py-2 bg-background border border-borders text-textMain text-xs font-semibold rounded hover:border-primary transition-colors flex items-center justify-center gap-2"
            >
              {isRepairing ? (
                <>
                  <span className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  Synthesizing Repair Proposal...
                </>
              ) : (
                '🔧 Propose Circuit Repair'
              )}
            </button>

            {repairBanner && (
              <div
                className={`p-2 text-xs rounded border ${
                  repairBanner.includes('✓')
                    ? 'bg-success/10 border-success/30 text-success'
                    : 'bg-warning/10 border-warning/30 text-warning'
                }`}
              >
                {repairBanner}
              </div>
            )}

            {repairError && (
              <div className="p-2 text-xs bg-error/10 border border-error/30 text-error rounded">
                {repairError}
              </div>
            )}

            {repairProposal && (
              <div className="p-3 bg-background border border-borders rounded space-y-3 text-xs">
                {/* Defect Category & Confidence */}
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-error/20 text-error">
                    Defect: {repairProposal.error_category.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] text-muted">
                    Confidence: {(repairProposal.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="font-semibold text-textMain text-[11px]">
                  {repairProposal.diagnosis_summary}
                </div>

                {/* Diff Summary Items */}
                {repairProposal.diff_summary.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted uppercase font-bold block">
                      Proposed Circuit Changes:
                    </span>
                    {repairProposal.diff_summary.map((change: string, idx: number) => (
                      <div
                        key={idx}
                        className="px-2 py-1 bg-panels border-l-2 border-primary text-[10px] font-mono text-textMain rounded"
                      >
                        {change}
                      </div>
                    ))}
                  </div>
                )}

                {/* Code Diff Block */}
                {repairProposal.code_diff && (
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted uppercase font-bold block">
                      Code Diff (Before / After):
                    </span>
                    <pre className="p-2 bg-panels border border-borders rounded font-mono text-[9px] overflow-x-auto text-textMain whitespace-pre leading-tight">
                      {repairProposal.code_diff.split('\n').map((line: string, i: number) => {
                        let color = 'text-textMain';
                        if (line.startsWith('+') && !line.startsWith('+++')) {
                          color = 'text-success font-semibold';
                        } else if (line.startsWith('-') && !line.startsWith('---')) {
                          color = 'text-error font-semibold';
                        } else if (line.startsWith('@@')) {
                          color = 'text-muted';
                        }
                        return (
                          <div key={i} className={color}>
                            {line}
                          </div>
                        );
                      })}
                    </pre>
                  </div>
                )}

                {/* Apply / Reject Controls */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={handleApplyRepair}
                    className="flex-1 py-1.5 bg-success text-white text-xs font-semibold rounded hover:bg-success/90 transition-colors"
                  >
                    ✓ Apply Repair
                  </button>
                  <button
                    onClick={handleRejectRepair}
                    className="flex-1 py-1.5 bg-error/10 border border-error/30 text-error text-xs font-semibold rounded hover:bg-error/20 transition-colors"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: OPTIMIZER */}
        {activeTab === 'optimize' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-textMain">AI Circuit Optimizer</h4>
                <p className="text-[10px] text-muted">
                  Algebraic cancellation, rotation merging & formal equivalence verification.
                </p>
              </div>
              <div className="flex items-center gap-1 text-[10px]">
                <span className="text-muted">Level:</span>
                {[1, 2, 3].map((lvl) => (
                  <button
                    key={lvl}
                    onClick={() => {
                      setOptLevel(lvl);
                      handleOptimize(lvl);
                    }}
                    className={`px-1.5 py-0.5 rounded border ${
                      optLevel === lvl
                        ? 'bg-primary text-white border-primary font-bold'
                        : 'bg-background border-borders text-muted hover:text-textMain'
                    }`}
                  >
                    L{lvl}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => handleOptimize(optLevel)}
              disabled={isOptimizing}
              className="w-full py-2 bg-primary text-white text-xs font-semibold rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isOptimizing ? 'Analyzing & Optimizing...' : '🚀 Run Circuit Optimization'}
            </button>

            {optBanner && (
              <div className="p-2 text-[11px] rounded bg-primary/10 border border-primary/30 text-primary">
                {optBanner}
              </div>
            )}

            {optError && (
              <div className="p-2 text-[11px] rounded bg-error/10 border border-error/30 text-error">
                {optError}
              </div>
            )}

            {optimizationResult && (
              <div className="space-y-3 p-3 bg-background border border-borders rounded-md">
                {/* Equivalence Badge */}
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-muted">Formal Verification:</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      optimizationResult.equivalent
                        ? 'bg-success/20 text-success border border-success/40'
                        : 'bg-error/20 text-error border border-error/40'
                    }`}
                  >
                    {optimizationResult.equivalent
                      ? `✓ Equivalent (Fidelity: ${((optimizationResult.fidelity ?? 1) * 100).toFixed(1)}%)`
                      : '✕ Equivalence Failed'}
                  </span>
                </div>

                {/* Metrics Comparison Grid */}
                {optimizationResult.metrics && (
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 bg-panels border border-borders rounded">
                      <div className="text-[10px] text-muted">Gates</div>
                      <div className="text-xs font-bold text-textMain mt-0.5">
                        {optimizationResult.metrics.original_gate_count} → {optimizationResult.metrics.optimized_gate_count}
                      </div>
                      <div className="text-[9px] text-success font-semibold mt-0.5">
                        -{optimizationResult.metrics.gate_reduction_percent}%
                      </div>
                    </div>
                    <div className="p-2 bg-panels border border-borders rounded">
                      <div className="text-[10px] text-muted">Depth</div>
                      <div className="text-xs font-bold text-textMain mt-0.5">
                        {optimizationResult.metrics.original_depth} → {optimizationResult.metrics.optimized_depth}
                      </div>
                      <div className="text-[9px] text-success font-semibold mt-0.5">
                        -{optimizationResult.metrics.depth_reduction_percent}%
                      </div>
                    </div>
                    <div className="p-2 bg-panels border border-borders rounded">
                      <div className="text-[10px] text-muted">CNOTs</div>
                      <div className="text-xs font-bold text-textMain mt-0.5">
                        {optimizationResult.metrics.original_cnot_count} → {optimizationResult.metrics.optimized_cnot_count}
                      </div>
                      <div className="text-[9px] text-success font-semibold mt-0.5">
                        -{optimizationResult.metrics.cnot_reduction_percent}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Transformations Applied */}
                {optimizationResult.transformations && optimizationResult.transformations.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted uppercase font-bold block">
                      Applied Transformations ({optimizationResult.transformations.length}):
                    </span>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {optimizationResult.transformations.map((t: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-1.5 bg-panels border border-borders rounded text-[10px] flex items-center justify-between"
                        >
                          <span className="text-textMain">{t.description}</span>
                          <span className="px-1 py-0.5 rounded bg-primary/20 text-primary font-mono text-[9px]">
                            {t.type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Explanation */}
                {optimizationResult.explanation && (
                  <div className="p-2 bg-panels border border-borders rounded text-[10px] text-textMain whitespace-pre-line leading-relaxed">
                    {optimizationResult.explanation}
                  </div>
                )}

                {/* Apply / Reject Controls */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={handleApplyOptimization}
                    disabled={!optimizationResult.equivalent}
                    className="flex-1 py-1.5 bg-success text-white text-xs font-semibold rounded hover:bg-success/90 disabled:opacity-40 transition-colors"
                  >
                    ✓ Apply Optimized Circuit
                  </button>
                  <button
                    onClick={handleRejectOptimization}
                    className="flex-1 py-1.5 bg-error/10 border border-error/30 text-error text-xs font-semibold rounded hover:bg-error/20 transition-colors"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
