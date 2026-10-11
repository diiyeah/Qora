from services.api.simulate.base import BackendAdapter
from packages.schema.models import Circuit
from services.api.errors import PlatformError

class qBraidAdapter(BackendAdapter):
    def __init__(self, fallback_adapter: BackendAdapter):
        self.fallback = fallback_adapter

    @property
    def name(self) -> str:
        return "qbraid_local"
        
    def capabilities(self) -> dict:
        return {
            "max_qubits": 20,
            "supports_statevector": True,
            "supports_noise": True
        }
        
    def run(self, circuit: Circuit, shots: int = 1024, noise: dict | None = None, seed: int | None = None) -> dict:
        try:
            # Simulate a qBraid cloud API call
            # In a real implementation, this would use qbraid.providers API keys 
            # and submit a job to their cloud infrastructure.
            
            # For Phase 1, we simulate a cloud timeout/failure to trigger the fallback
            raise Exception("qBraid cloud API timeout")
            
        except Exception as e:
            # Fallback cleanly to the provided local simulator (e.g. Aer)
            try:
                result = self.fallback.run(circuit, shots, noise, seed)
                # Annotate the result to show it used the fallback
                result["backend"]["note"] = f"Fell back from qBraid due to: {str(e)}"
                return result
            except Exception as fallback_e:
                raise PlatformError("backend_unavailable", f"qBraid failed and fallback also failed: {str(fallback_e)}")
