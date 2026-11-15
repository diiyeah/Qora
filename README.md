# Qora

Backend for the **AI-Powered Quantum Computing Development, Optimization and Adaptive Learning Platform**. This repository currently implements **Phase 1, Week 1** for Member A: the Python contracts, FastAPI foundation, and an Aer simulation smoke test. Member B owns `apps/web`; no frontend changes are included.

## Week 1 milestone

- Python 3.11+ package with locked dependencies, FastAPI, Pydantic v2, Qiskit, and Qiskit Aer.
- Shared circuit contract and checked-in JSON Schema for frontend consumers.
- Versioned health and simulation endpoints, with the originally requested unversioned aliases.
- Hardcoded Bell-circuit simulation with shot counts, seed support, and qubit 0 on the left.
- Structured API errors and a Python simulation function usable without HTTP.
- Docker/Compose runtime and GitHub Actions checks on pushes and pull requests.
- Tests covering schema validation, Bell counts, asymmetric X-flips, reproducibility, failure handling, and OpenAPI response contracts; strict mypy checks.

Validation: 64 tests and strict mypy pass locally on Windows/Python 3.13. GitHub Actions verifies Python 3.11 and 3.13, plus Docker build/start and live HTTP checks.

Week 1 accepts **only the fixed Bell circuit** at `/simulate`. Arbitrary circuit input, probabilities, statevectors, and fixtures are Week 2 work. No AI/LLM, learner models, or dashboards are implemented.

## Repository layout

```text
services/api/
  main.py                 FastAPI application
  errors.py               Structured engine errors
  simulate/               Importable Aer engine
  convert/                Reserved for Weeks 2/4
  sandbox/                Reserved for Week 3
  analyze/                Reserved for Week 5
packages/schema/
  models.py               Circuit models and validation
  api.py                  Week 1 request/result/error models
  circuit.schema.json     Exported circuit contract
data/fixtures/            Reserved for Week 2 fixtures
tests/                    pytest suite
scripts/smoke_api.py       Checks a running API
docker-compose.yml        API container configuration
.github/workflows/        Backend CI
```

## Run locally

Install Python 3.11 or newer. From the repository root:

```shell
python -m pip install --user uv==0.12.22
python -m uv sync --locked
python -m uv run --locked uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

`uv` creates `.venv` and installs the versions from `uv.lock`, including Qiskit/Aer and development tools. The lock includes separate dependency resolutions where Python 3.11 needs older compatible releases. There are no cloud credentials or environment variables required for Week 1.

- [Interactive API documentation](http://127.0.0.1:8000/docs)
- [Alternative API reference](http://127.0.0.1:8000/redoc)
- [OpenAPI JSON](http://127.0.0.1:8000/openapi.json)

## Run with Docker

Install Docker with the Compose v2 plugin and start the Docker engine:

```shell
docker compose up --build --detach --wait
docker compose logs --follow api
```

The container uses Python 3.13, installs locked runtime dependencies, runs as a non-root user, and checks `/v1/health`. It exposes the API at `http://127.0.0.1:8000`. Set `API_PORT` to change the host port. Stop it with `docker compose down`. It does not build or copy `apps/web`.

## Week 1 API reference

`/v1` is the documented API version. `/health` and `/simulate` are aliases for compatibility with the project endpoint list. Both aliases behave identically to their `/v1` counterparts.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/v1/health` | API liveness; does not probe simulator readiness |
| POST | `/v1/simulate` | Shot counts for the fixed two-qubit Bell circuit |

Health response:

```json
{"status": "ok", "version": "0.1.0"}
```

Simulation request:

```json
{"backend": "aer", "shots": 1024, "seed": 17}
```

`backend` defaults to `"aer"` and is the only available backend. `shots` defaults to 1024 and must be an integer from 1 to 100000. `seed` defaults to `null`; an integer from 0 to 4294967295 makes sampling reproducible within the same dependency environment. Unknown fields, including `circuit` and `noise`, are rejected until their planned implementation.

The circuit applies `h` to qubit 0, then `cx` from qubit 0 to qubit 1, and measures both qubits into their matching classical bits. Example response (counts are illustrative):

```json
{
  "circuit": "bell",
  "counts": {"00": 510, "11": 514},
  "shots": 1024,
  "seed": 17,
  "backend": {
    "name": "aer",
    "version": "0.17.2",
    "framework": "qiskit",
    "framework_version": "2.5.2"
  }
}
```

Backend versions are read from the installed packages. Counts sum to the requested shots. **Qubit 0 is the leftmost bit**: an X gate on qubit 0 alone produces `10`, and X on qubit 1 alone produces `01`. The Week 1 engine reverses Qiskit's output for its identity measurement mapping; general measurement mapping is Week 2 work.

Invalid requests return HTTP 422. Simulator failures return 503; unexpected service failures return 500. Responses use this envelope without stack traces:

```json
{
  "error": {
    "type": "syntax",
    "line": null,
    "message": "Invalid request.",
    "details": {"issues": [{"location": ["body", "shots"], "message": "Input should be greater than or equal to 1", "type": "greater_than_equal"}]}
  }
}
```

An unsupported backend uses `backend_unavailable`. The shared error contract also reserves `invalid_gate`, `qubit_out_of_range`, `measurement`, `timeout`, and `sandbox_violation` for later endpoints. `line` is null in Week 1; code execution with source line reporting arrives in Week 3.

PowerShell request example:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/simulate `
  -ContentType 'application/json' -Body '{"shots":1024,"seed":17}'
```

## Shared circuit contract

Frontend consumers can use [`packages/schema/circuit.schema.json`](packages/schema/circuit.schema.json). Python consumers import the models directly:

```python
from packages.schema import Circuit

circuit = Circuit.model_validate({
    "num_qubits": 2,
    "num_clbits": 2,
    "gates": [
        {"name": "h", "qubits": [0], "params": [], "layer": 0},
        {"name": "cx", "qubits": [0, 1], "params": [], "layer": 1},
    ],
    "measurements": [{"qubit": 0, "clbit": 0}, {"qubit": 1, "clbit": 1}],
    "metadata": {"framework": "qiskit", "task_id": None},
})
```

Supported gates: `h`, `x`, `y`, `z`, `s`, `sdg`, `t`, `tdg`, `rx`, `ry`, `rz`, `p`, `cx`, `cz`, `swap`, `ccx`. Rotations and `p` require one finite angle parameter; other gates require none. Gates must have the correct number of distinct qubits. Qubit and classical-bit indices must be in range. Zero classical bits are valid for an unmeasured circuit. Gate `layer` is a nonnegative drawing position; it does not establish computed circuit depth. Measurements occur after all gates.

JSON Schema validates structure, field types, and gate names. The Python models additionally enforce cross-field rules such as arity, parameter counts, and indices relative to circuit size. Direct model validation raises Pydantic `ValidationError`; HTTP endpoints translate request failures into the shared error envelope.

Regenerate or verify the exported contract:

```shell
python -m uv run --locked python -m packages.schema.export
python -m uv run --locked python -m packages.schema.export --check
```

## Python engine interface

```python
from services.api.simulate import simulate_bell
from services.api.errors import PlatformError

try:
    result = simulate_bell(shots=1024, seed=17)
    print(result.counts)
except PlatformError as error:
    print(error.error.model_dump())
```

The engine has no FastAPI dependency in its simulation implementation. The full circuit entry point and multi-backend interface will be added in their planned weeks.

## Validation and CI

```shell
python -m uv run --locked pytest
python -m uv run --locked mypy
python -m uv run --locked python -m packages.schema.export --check
```

With the API running in another terminal:

```shell
python scripts/smoke_api.py
```

[Backend CI](https://github.com/diiyeah/Qora/actions/workflows/backend.yml) runs pytest, strict mypy, and schema-drift checks on Python 3.11 and 3.13. Its separate Docker job builds and starts Compose, waits for the container health check, and exercises real HTTP health, seeded simulation, route aliases, and structured validation errors. GitHub Actions is also the Docker validation environment when Docker is unavailable on the local workstation.

## Phase 1 Features Completed

| Week | Scope | Status |
| --- | --- | --- |
| 1 | FastAPI skeleton, schema validation, fixed Bell circuit on Aer | ✅ Done |
| 2 | Arbitrary Aer circuits, converter, probabilities, statevectors | ✅ Done |
| 3 | Per-gate states and isolated code execution sandbox | ✅ Done |
| 4 | Qiskit/OpenQASM round trips and conversion API | ✅ Done |
| 5 | Circuit analysis and metrics verified against Qiskit | ✅ Done |
| 6 | Backend abstraction layer and PennyLane adapter | ✅ Done |
| 7 | Cirq adapter, qBraid fallback adapter, backend discovery | ✅ Done |
| 8 | Noise injection, resource estimates, TVD checks, API freeze | ✅ Done |

Phase 1 is fully complete for Member A. All implementation steps have been documented and the APIs are frozen for Phase 2.

Implementation references: [AerSimulator documentation](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html), [FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/), and [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).
