import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from packages.schema import Circuit, Gate
from packages.schema.export import SCHEMA_PATH, rendered_schema
from packages.schema.models import GATE_ARITY, PARAMETER_GATES, GateName


def bell_payload() -> dict[str, Any]:
    return {
        "num_qubits": 2, "num_clbits": 2,
        "gates": [
            {"name": "h", "qubits": [0], "params": [], "layer": 0},
            {"name": "cx", "qubits": [0, 1], "params": [], "layer": 1},
        ],
        "measurements": [{"qubit": 0, "clbit": 0}, {"qubit": 1, "clbit": 1}],
        "metadata": {"framework": "qiskit", "task_id": None},
    }


def test_exact_contract_and_export() -> None:
    payload = bell_payload()
    assert Circuit.model_validate(payload).model_dump(mode="json") == payload
    assert SCHEMA_PATH.read_text(encoding="utf-8") == rendered_schema()
    schema = json.loads(rendered_schema())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name", sorted(GATE_ARITY))
def test_supported_gates(name: GateName) -> None:
    gate = Gate.model_validate({
        "name": name,
        "qubits": list(range(GATE_ARITY[name])),
        "params": [0.25] if name in PARAMETER_GATES else [],
        "layer": 0,
    })
    assert gate.name == name


@pytest.mark.parametrize("gate", [
    {"name": "unknown", "qubits": [0], "params": [], "layer": 0},
    {"name": "h", "qubits": [0, 1], "params": [], "layer": 0},
    {"name": "cx", "qubits": [0, 0], "params": [], "layer": 0},
    {"name": "ccx", "qubits": [0, 1], "params": [], "layer": 0},
    {"name": "rx", "qubits": [0], "params": [], "layer": 0},
    {"name": "ry", "qubits": [0], "params": [1, 2], "layer": 0},
    {"name": "h", "qubits": [0], "params": [1], "layer": 0},
    {"name": "rz", "qubits": [0], "params": [float("nan")], "layer": 0},
    {"name": "p", "qubits": [0], "params": [float("inf")], "layer": 0},
    {"name": "x", "qubits": [-1], "params": [], "layer": 0},
    {"name": "x", "qubits": [True], "params": [], "layer": 0},
    {"name": "x", "qubits": [0.5], "params": [], "layer": 0},
    {"name": "x", "qubits": [0], "params": [], "layer": -1},
])
def test_invalid_gates(gate: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Gate.model_validate(gate)


@pytest.mark.parametrize(("field", "value"), [
    ("num_qubits", 0), ("num_qubits", -1), ("num_qubits", True),
    ("num_qubits", "2"), ("num_clbits", -1), ("num_clbits", 1.5),
    ("extra", "unexpected"),
])
def test_invalid_circuit_shape(field: str, value: Any) -> None:
    payload = bell_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        Circuit.model_validate(payload)


@pytest.mark.parametrize(("section", "index", "field", "value", "error_type"), [
    ("gates", 0, "qubits", [2], "qubit_out_of_range"),
    ("measurements", 0, "qubit", 2, "qubit_out_of_range"),
    ("measurements", 0, "clbit", 2, "measurement"),
])
def test_out_of_range(
    section: str, index: int, field: str, value: Any, error_type: str,
) -> None:
    payload = deepcopy(bell_payload())
    payload[section][index][field] = value
    with pytest.raises(ValidationError) as caught:
        Circuit.model_validate(payload)
    assert caught.value.errors()[0]["type"] == error_type


def test_unmeasured_circuit_and_remapped_measurements() -> None:
    payload = bell_payload()
    payload.update(num_clbits=0, measurements=[])
    assert Circuit.model_validate(payload).num_clbits == 0
    payload.update(num_clbits=2, measurements=[{"qubit": 0, "clbit": 1}])
    assert Circuit.model_validate(payload).measurements[0].clbit == 1
