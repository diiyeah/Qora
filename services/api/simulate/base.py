from abc import ABC, abstractmethod
from typing import Any
from packages.schema.models import Circuit

class BackendAdapter(ABC):
    """Abstract base class for quantum backend adapters."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier of the backend."""
        pass
        
    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return the capabilities of this backend (max_qubits, supports_noise, etc)."""
        pass
        
    @abstractmethod
    def run(self, circuit: Circuit, shots: int = 1024, noise: dict | None = None, seed: int | None = None) -> dict:
        """
        Run the given circuit schema on the target backend.
        
        Returns:
            dict containing at minimum 'counts' with Qiskit-style bit-ordering (qubit 0 on the right, or left depending on normalisation, matching Qiskit's reversed default).
        """
        pass
