# Quantum Lab - Frontend (Member B)

This directory contains the Next.js frontend application for the Quantum Lab project, built for Phase 1. 

## Implemented Features

### Interactive Quantum Learning Platform & IDE
- **App Shell & Layout**: Next.js 15 application with a responsive, dark-themed layout.
- **Authentication**: Basic Login and Sign-up UI routes.
- **Development Mode**: Integrated workspace housing both the Circuit Builder and the Code Editor.
- **Workspace Persistence**: Mocked API endpoints to save the current workspace state (circuit, code, selected backend).

### Quantum Circuit Builder
- **Gate Palette & Canvas**: Drag-and-drop circuit builder using SVG.
- **Supported Gates**: Supports adding/removing `h, x, y, z, s, t, rx, ry, rz, cx, swap` gates and measurements.
- **Interactivity**: Ability to add/remove qubits, click gates to delete them, and input rotation parameters or target qubits via browser prompts.
- **Snap-to-Grid**: Gates snap into discrete layers to maintain the schema matrix format.

### Quantum Code Editor
- **Monaco Editor**: Integrated `@monaco-editor/react` with Python syntax highlighting.
- **Framework Selector**: Dropdown to switch between code snippet templates for Qiskit, PennyLane, and Cirq.
- **Error Highlighting**: Integrates with structured backend errors to display red squiggly markers on specific lines of code.

### Code-Circuit Synchronization & Export
- **Two-way Sync**: Code automatically updates when building the circuit (via mock `/convert`), and the circuit updates when modifying code (via mock `/execute-code`).
- **OpenQASM Export**: A one-click button to download the current circuit state as an `OPENQASM 2.0` file.

### Multi-Backend Simulation Engine (UI)
- **Backend Selector**: Dropdown populated from the API (Aer Simulator, PennyLane Default, Cirq, qBraid).
- **Side-by-Side Comparison**: Ability to select a "Compare With" backend, rendering a split-screen view of results from two different backends simultaneously.
- **Noise Simulation**: Toggle switch to inject depolarizing noise into the simulation payload.

### Visualization Engine & Metrics
- **Histograms**: Interactive bar charts built with `recharts` for Measurement Counts and Probabilities.
- **Statevector View**: Formatted table displaying the final statevector's real and imaginary amplitudes.
- **Metrics Panel**: Displays Qubit count, Circuit Depth, Total Gates, CNOT count, and Gate-type breakdown.
- **Bloch Sphere & Evolution**: Custom SVG Bloch spheres for each qubit showing the state vector and calculating purity for entangled/mixed states. A slider allows scrubbing through the circuit's gate-by-gate state evolution.

### Accessibility
- **ARIA Integration**: Added ARIA labels, roles, and keyboard navigation to the interactive SVG Circuit Canvas.

## Outstanding Items / Not Yet Implemented
* **Component & Integration Tests**: Playwright end-to-end tests and unit tests for the React components have not been written yet.
* **Real Backend Integration**: The application currently relies on Next.js Route Handler mocks (`/api/simulate`, `/api/convert`, etc.) and is ready to be pointed to Member A's actual FastAPI backend.

## Getting Started

```bash
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
