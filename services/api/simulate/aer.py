"""Week 1 Aer smoke test; general circuit simulation is a Week 2 task."""

from importlib.metadata import version

from pydantic import ValidationError
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from packages.schema.api import BackendInfo, SimulationRequest, SimulationResult
from services.api.errors import PlatformError


def _run_counts(circuit: QuantumCircuit, shots: int, seed: int | None) -> dict[str, int]:
    """Run a measured circuit with the identity mapping q_i -> c_i.

    Qiskit prints the most significant classical bit on the left. Reverse at
    this boundary so wire/qubit 0 is on the left for our Week 1 circuits.
    General measurement mappings will be handled by the Week 2 converter.
    """
    try:
        simulator = AerSimulator(max_parallel_threads=1)
        result = simulator.run(circuit, shots=shots, seed_simulator=seed).result()
        if not result.success:
            raise PlatformError(
                "backend_unavailable", "Aer could not complete the simulation.",
                status_code=503,
            )
        counts = result.get_counts()
        return {str(bits).replace(" ", "")[::-1]: int(count) for bits, count in counts.items()}
    except PlatformError:
        raise
    except Exception:
        raise PlatformError(
            "backend_unavailable", "Aer is unavailable or could not run the circuit.",
            status_code=503,
        ) from None


def simulate_bell(shots: int = 1024, seed: int | None = None) -> SimulationResult:
    """Simulate H(q0), CX(q0, q1), then measure both wires.

    This importable function is independent of FastAPI. Invalid parameters or
    simulator failures raise PlatformError with a structured ``error`` field.
    """
    try:
        request = SimulationRequest(shots=shots, seed=seed)
    except ValidationError:
        raise PlatformError(
            "syntax", "Shots must be an integer from 1 to 100000 and seed must be null "
            "or an integer from 0 to 4294967295.",
        ) from None
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return SimulationResult(
        counts=_run_counts(circuit, request.shots, request.seed),
        shots=request.shots,
        seed=request.seed,
        backend=BackendInfo(version=version("qiskit-aer"), framework_version=version("qiskit")),
    )
