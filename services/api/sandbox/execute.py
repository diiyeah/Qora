import subprocess
import json
import os
import tempfile
from services.api.errors import PlatformError

def execute_sandboxed_code(code: str) -> dict:
    """Execute Python code in an isolated subprocess with strict limits."""
    
    # Pre-parse the code to prevent dangerous imports (basic static analysis)
    banned_terms = ['import os', 'import sys', 'import subprocess', '__import__', 'eval(', 'exec(']
    for term in banned_terms:
        if term in code:
            raise PlatformError("sandbox_violation", f"Use of forbidden term '{term}' detected.")
            
    # Wrap user code to output the JSON schema
    wrapped_code = f"""
import json
import sys
from qiskit import QuantumCircuit
import warnings
warnings.filterwarnings('ignore')

try:
{chr(10).join(['    ' + line for line in code.split(chr(10))])}
    
    # After user code runs, try to find 'circuit' object
    if 'circuit' in locals() and isinstance(circuit, QuantumCircuit):
        # Convert Qiskit circuit to our schema format (simplified mockup)
        output = {{
            "num_qubits": circuit.num_qubits,
            "num_clbits": circuit.num_clbits,
            "gates": [{"name": inst.operation.name, "qubits": [q._index for q in inst.qubits], "params": inst.operation.params} for inst in circuit.data if inst.operation.name != 'measure'],
            "measurements": [{"qubit": inst.qubits[0]._index, "clbit": inst.clbits[0]._index} for inst in circuit.data if inst.operation.name == 'measure']
        }}
        print(json.dumps({{"circuit": output}}))
    else:
        print(json.dumps({{"error": "Variable 'circuit' of type QuantumCircuit not found"}}))
except Exception as e:
    import traceback
    tb = traceback.extract_tb(sys.exc_info()[2])
    line_no = tb[-1].lineno if tb else None
    # Adjust line number to account for wrapper indentation
    if line_no:
        line_no -= 8 
    print(json.dumps({{"error": {{"type": "syntax", "line": line_no, "message": str(e)}}}}))
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(wrapped_code)
        temp_file = f.name
        
    try:
        # Run subprocess with timeout
        # In a real environment, we would use cgroups or runc/docker for proper resource isolation
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if result.returncode != 0 and not result.stdout:
            raise PlatformError("sandbox_violation", "Process crashed or was killed.")
            
        try:
            output = json.loads(result.stdout)
            if "error" in output:
                if isinstance(output["error"], dict):
                    raise PlatformError(output["error"]["type"], output["error"]["message"])
                else:
                    raise PlatformError("syntax", output["error"])
            return output["circuit"]
        except json.JSONDecodeError:
            raise PlatformError("sandbox_violation", f"Invalid output from sandbox: {result.stdout}")
            
    except subprocess.TimeoutExpired:
        raise PlatformError("timeout", "Code execution exceeded the 5-second timeout limit.")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
