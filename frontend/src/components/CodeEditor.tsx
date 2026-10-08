import React, { useEffect, useRef, useState } from 'react';
import Editor, { useMonaco } from '@monaco-editor/react';

interface CodeEditorProps {
  code: string;
  onChange: (value: string | undefined) => void;
  onRun: () => void;
  isLoading: boolean;
  errorLine?: number | null;
  errorMessage?: string | null;
}

const SNIPPETS: Record<string, string> = {
  qiskit: "from qiskit import QuantumCircuit\n\ncircuit = QuantumCircuit(2, 2)\ncircuit.h(0)\ncircuit.cx(0, 1)\ncircuit.measure([0, 1], [0, 1])",
  pennylane: "import pennylane as qml\n\ndev = qml.device('default.qubit', wires=2)\n@qml.qnode(dev)\ndef circuit():\n    qml.Hadamard(wires=0)\n    qml.CNOT(wires=[0, 1])\n    return qml.probs(wires=[0, 1])",
  cirq: "import cirq\n\nq0, q1 = cirq.LineQubit.range(2)\ncircuit = cirq.Circuit(\n    cirq.H(q0),\n    cirq.CNOT(q0, q1),\n    cirq.measure(q0, q1, key='result')\n)"
};

export function CodeEditor({ code, onChange, onRun, isLoading, errorLine, errorMessage }: CodeEditorProps) {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const [framework, setFramework] = useState('qiskit');

  useEffect(() => {
    if (monaco && editorRef.current) {
      const model = editorRef.current.getModel();
      if (model) {
        if (errorLine && errorMessage) {
          monaco.editor.setModelMarkers(model, "owner", [{
            startLineNumber: errorLine,
            startColumn: 1,
            endLineNumber: errorLine,
            endColumn: 100,
            message: errorMessage,
            severity: monaco.MarkerSeverity.Error
          }]);
        } else {
          monaco.editor.setModelMarkers(model, "owner", []);
        }
      }
    }
  }, [monaco, errorLine, errorMessage, code]);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleFrameworkChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const fw = e.target.value;
    setFramework(fw);
    onChange(SNIPPETS[fw]);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-2">
        <div className="flex gap-2 items-center">
          <span className="text-sm text-gray-400">main.py</span>
          <select 
            value={framework} 
            onChange={handleFrameworkChange}
            className="ml-4 bg-gray-800 text-sm text-gray-200 border border-gray-700 rounded px-2 py-1"
          >
            <option value="qiskit">Qiskit</option>
            <option value="pennylane">PennyLane</option>
            <option value="cirq">Cirq</option>
          </select>
        </div>
        <button
          onClick={onRun}
          disabled={isLoading}
          className="px-4 py-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded text-sm transition-colors"
        >
          {isLoading ? 'Running...' : 'Run Code'}
        </button>
      </div>
      <div className="flex-1 border border-gray-700 rounded overflow-hidden">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={onChange}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            padding: { top: 16 },
          }}
        />
      </div>
    </div>
  );
}
