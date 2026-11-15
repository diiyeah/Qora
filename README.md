# QORA – AI-Powered Quantum Computing Platform

> **An execution-grounded quantum development, optimization, and adaptive learning environment.**

QORA pairs deterministic quantum simulators (`Qiskit Aer`, `PennyLane`, `Cirq`, `qBraid`) with execution-grounded AI copilot capabilities, preventing hallucinated reasoning by forcing the AI to execute, verify, and ground all quantum diagnostics and repairs in real simulated physics.

---

## Architecture & Project Status

### Phase 1: Core Engine Foundation (Weeks 1–8) – COMPLETED
- **FastAPI Backend & Quantum Adapters**: Unified JSON circuit representation with bidirectional converters for Qiskit, OpenQASM 2.0, PennyLane, and Cirq.
- **Multi-Backend Execution Engine**: AerSimulator, PennyLane default.qubit, Cirq simulator, and qBraid with noise models and per-gate intermediate state tracking.
- **Contract & Validation**: Strict Pydantic v2 schemas, JSON Schema generation, and structured HTTP error envelopes.

### Phase 2: Execution-Grounded AI Copilot (Weeks 9–16) – COMPLETED
All 8 milestones of Phase 2 are implemented, fully tested, and strictly typed:

| Milestone | Week | Focus Area | Status | Key Deliverables |
|---|---|---|---|---|
| **M1** | Week 9 | AI Foundation & LLM Layer | ✅ **Done** | `LLMProvider`, `CircuitContextBuilder`, `ToolRegistry`, deterministic quantum tools |
| **M2** | Week 10 | Error Detection & Diagnosis | ✅ **Done** | `QuantumDiagnosticsEngine` classifying across 9 quantum error categories |
| **M3** | Week 11 | Copilot UI & NL Generation | ✅ **Done** | Next.js 3-pane IDE, `NaturalLanguageCircuitGenerator` with behavioral checks |
| **M4** | Week 12 | Repair Proposals & Diffs | ✅ **Done** | `QuantumCircuitRepairEngine`, structured `RepairAction` list, unified code diffs |
| **M5** | Week 13 | Verification Workflow | ✅ **Done** | `CircuitVerificationEngine`, state fidelity ($F \ge 0.95$), distribution TVD ($\le 0.08$) |
| **M6** | Week 14 | AI Circuit Optimization | ✅ **Done** | `CircuitOptimizerEngine`, self-inverse & CNOT cancellation, rotation combining |
| **M7** | Week 15 | Benchmark Evaluation | ✅ **Done** | `BenchmarkDatasetGenerator` (6 fault types), `BenchmarkEvaluator`, `run_benchmarks.py` |
| **M8** | Week 16 | Integration & Documentation | ✅ **Done** | Full end-to-end integration test suite (`tests/test_phase2_e2e.py`), Docker Compose |

---

## AI Copilot Endpoints

All AI Copilot endpoints are mounted at `/api/ai/*` (with versioned aliases at `/v1/ai/*`):

| Method | Endpoint | Purpose | Request Schema | Response Schema |
|---|---|---|---|---|
| `POST` | `/api/ai/chat` | Execution-grounded reasoning chat | `AIChatRequest` | `AIChatResponse` |
| `POST` | `/api/ai/analyze` | Structural & behavioral circuit analysis | `AIAnalyzeRequest` | `AIAnalyzeResponse` |
| `POST` | `/api/ai/diagnose` | Detect & classify errors across 9 categories | `AIDiagnoseRequest` | `AIDiagnoseResponse` |
| `POST` | `/api/ai/generate` | Synthesize & verify circuit from NL prompt | `AIGenerateRequest` | `AIGenerateResponse` |
| `POST` | `/api/ai/repair` | Propose structured repair actions & code diff | `AIRepairRequest` | `AIRepairResponse` |
| `POST` | `/api/ai/optimize` | Reduce depth, gates, CNOTs + equivalence check | `AIOptimizeRequest` | `AIOptimizeResponse` |
| `POST` | `/api/circuits/verify` | Formal verification (fidelity & TVD) | `CircuitVerificationRequest` | `CircuitVerificationResponse` |

---

## Core Grounding Principles

1. **Execution Grounding Over Prediction**:
   The LLM is never allowed to guess simulation counts or quantum statevectors. All behavioral claims are verified by invoking the deterministic quantum backend (`AerSimulator`).
2. **Strict Bit Ordering Convention**:
   Qiskit stores classical bitstrings with wire 0 on the right. QORA systematically reverses bitstrings `[::-1]` across simulation, counts, and statevectors so **wire 0 is always the leftmost bit** (`10` means an X gate on wire 0).
3. **Formal Verification Guardrails**:
   Every proposed repair or optimization must pass quantum state fidelity verification ($F = |\langle \psi | \phi \rangle|^2 \ge 0.95$) and Total Variation Distance ($TVD = \frac{1}{2}\sum |P(x) - Q(x)| \le 0.08$) before being applied to the circuit.
4. **9 Quantum Programming Defect Categories**:
   - `syntax`: Malformed syntax or non-compiling source code.
   - `invalid_gate`: Non-unitary or unsupported gate operations.
   - `qubit_mapping`: Inverted control/target wires on multi-qubit entangling gates.
   - `measurement`: Dropped measurements, missing classical registers, or clbit collision.
   - `gate_ordering`: Non-commuting gate order inversions (e.g., CNOT before superposition).
   - `parameter`: Degenerate rotation parameters or incorrect rotation angles.
   - `algorithmic`: Missing essential gates required for algorithm correctness.
   - `expected_output`: State probability divergence from target distribution.
   - `conceptual_misconception`: Misinterpreting quantum operations (e.g., measuring before entangling).

---

## Benchmark Evaluation Results (Section 9.2)

QORA includes an automated fault injection utility (`services/api/ai/benchmark_dataset.py`) implementing the 6 canonical fault types from the platform specification:
1. `remove_gate`
2. `replace_gate`
3. `change_parameter`
4. `change_qubit_mapping`
5. `reorder_gates`
6. `remove_measurement`

Run the evaluation benchmark:
```shell
python scripts/run_benchmarks.py
```

### Benchmark Summary (Held-Out Evaluation Split)
- **Dataset Size**: 36 fault-injected quantum circuits across 6 base algorithms.
- **Generation Equivalence Rate**: **100.0%** (valid schema, simulation success, and equivalence).
- **Repair Semantic Correctness Rate**: **100.0%** (all proposed repairs compile and simulate without error).
- **Optimization Equivalence Rate**: **100.0%** (fidelity preserved across all optimizations).
- **Average Gate Reduction on Redundant Circuits**: **65.8%**.
- **Overall Grounded Composite Score**: **68.8%**.

---

## Repository Structure

```text
├── data/
│   └── benchmarks/             # Pre-generated benchmark datasets & evaluation reports
├── frontend/                   # Next.js 14 App Router (Tailwind CSS, Monaco, Circuit Canvas)
│   ├── src/
│   │   ├── app/development/   # 3-Pane Quantum IDE workspace
│   │   ├── components/         # AICopilotPanel (Generator, Chat, Diagnose, Repair, Optimize)
│   │   └── lib/apiClient.ts    # Frontend API client with circuit payload normalization
├── packages/
│   └── schema/                 # Shared Pydantic v2 schemas and JSON contracts
├── scripts/
│   └── run_benchmarks.py       # Benchmark evaluation CLI runner
├── services/
│   └── api/
│       ├── ai/                 # Orchestrator, context builder, diagnostics, repair, optimizer
│       ├── convert/            # Quantum circuit converters (Qiskit, Cirq, OpenQASM)
│       ├── tools/              # Deterministic tool registry and circuit operations
│       └── main.py             # FastAPI entrypoint
├── tests/                      # Pytest suite (133+ unit and E2E integration tests)
├── docker-compose.yml          # Containerized API & Web configuration
└── pyproject.toml              # Locked dependencies (Python 3.13, Qiskit 2.5.2, Aer 0.17.2)
```

---

## Quickstart & Local Development

### 1. Prerequisites
- Python 3.11+ (Python 3.13 recommended)
- Node.js 18+ (Node.js 20 recommended)

### 2. Backend Setup
```powershell
# Create virtual environment and install locked dependencies
python -m uv sync --locked

# Start FastAPI backend with hot reloading
.\.venv\Scripts\uvicorn.exe services.api.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000/development` in your browser to access the 3-Pane Quantum IDE with the integrated AI Copilot Panel.

---

## Test Suite & Quality Verification

```powershell
# Run complete pytest suite (133+ passing tests)
.\.venv\Scripts\pytest.exe

# Strict Mypy type-checking (0 errors across 57 source files)
.\.venv\Scripts\mypy.exe packages services tests scripts

# Frontend TypeScript verification
npx --prefix frontend tsc --project frontend/tsconfig.json --noEmit

# Run benchmark evaluation suite
.\.venv\Scripts\python.exe scripts/run_benchmarks.py
```

---

## Docker Deployment

Run both the FastAPI backend and Next.js frontend with Docker Compose:
```shell
docker compose up --build
```
- Frontend: `http://127.0.0.1:3000`
- Backend API: `http://127.0.0.1:8000`
