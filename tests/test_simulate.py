from typing import Any

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from qiskit import QuantumCircuit

from packages.schema.api import SimulationResult
from services.api.errors import PlatformError
from services.api.main import app
from services.api.simulate import simulate_bell
from services.api.simulate.aer import _run_counts


def test_bell_known_answer_and_seed() -> None:
    result = simulate_bell(shots=4096, seed=17)
    assert sum(result.counts.values()) == 4096
    assert set(result.counts) == {"00", "11"}
    assert abs(result.counts["00"] / 4096 - 0.5) < 0.05
    assert simulate_bell(shots=4096, seed=17).counts == result.counts
    assert result.backend.name == "aer"
    assert result.backend.version


@pytest.mark.parametrize(("qubit", "expected"), [(0, "10"), (1, "01")])
def test_asymmetric_wire_order(qubit: int, expected: str) -> None:
    circuit = QuantumCircuit(2, 2)
    circuit.x(qubit)
    circuit.measure([0, 1], [0, 1])
    assert _run_counts(circuit, shots=64, seed=0) == {expected: 64}


@pytest.mark.parametrize("path", ["/simulate", "/v1/simulate"])
def test_simulate_endpoint(path: str) -> None:
    with TestClient(app) as client:
        response = client.post(path, json={"shots": 256, "seed": 0, "backend": "aer"})
    assert response.status_code == 200
    result = SimulationResult.model_validate(response.json())
    assert sum(result.counts.values()) == 256
    assert result.seed == 0


@pytest.mark.parametrize(("body", "error_type"), [
    ({"shots": 0}, "syntax"), ({"shots": 100001}, "syntax"),
    ({"shots": True}, "syntax"), ({"shots": "256"}, "syntax"),
    ({"shots": 1.5}, "syntax"), ({"seed": -1}, "syntax"),
    ({"seed": 2**32}, "syntax"), ({"seed": False}, "syntax"),
    ({"backend": "cirq"}, "backend_unavailable"),
    ({"circuit": {}}, "syntax"),
])
def test_structured_validation(body: dict[str, Any], error_type: str) -> None:
    with TestClient(app) as client:
        response = client.post("/simulate", json=body)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["type"] == error_type
    assert error["line"] is None
    assert isinstance(error["details"], dict)
    assert "traceback" not in response.text.lower()


def test_direct_engine_validates_request() -> None:
    with pytest.raises(PlatformError) as caught:
        simulate_bell(shots=-1)
    assert caught.value.error.type == "syntax"


def test_backend_failure_is_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_backend(**kwargs: Any) -> None:
        raise RuntimeError("secret implementation detail")

    monkeypatch.setattr("services.api.simulate.aer.AerSimulator", broken_backend)
    with TestClient(app) as client:
        response = client.post("/simulate", json={"shots": 16})
        spec = client.get("/openapi.json").json()
    assert response.status_code == 503
    assert response.json()["error"]["type"] == "backend_unavailable"
    assert "secret" not in response.text
    schema = {
        **spec["paths"]["/v1/simulate"]["post"]["responses"]["503"]["content"]["application/json"]["schema"],
        "components": spec["components"],
    }
    Draft202012Validator(schema).validate(response.json())


def test_unexpected_failure_matches_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_failure(shots: int, seed: int | None) -> SimulationResult:
        raise RuntimeError("private service details")

    monkeypatch.setattr("services.api.main.simulate_bell", unexpected_failure)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/v1/simulate", json={"shots": 16})
        spec = client.get("/openapi.json").json()
    assert response.status_code == 500
    assert response.json()["error"]["type"] == "backend_unavailable"
    assert "private" not in response.text
    schema = {
        **spec["paths"]["/v1/simulate"]["post"]["responses"]["500"]["content"]["application/json"]["schema"],
        "components": spec["components"],
    }
    Draft202012Validator(schema).validate(response.json())


def test_malformed_json_and_unknown_route() -> None:
    with TestClient(app) as client:
        malformed = client.post("/simulate", content="{", headers={"Content-Type": "application/json"})
        missing = client.get("/does-not-exist")
    assert malformed.status_code == 422
    assert malformed.json()["error"]["type"] == "syntax"
    assert missing.status_code == 404
    assert missing.json()["error"]["type"] == "syntax"


def test_responses_match_openapi() -> None:
    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()
        response = client.post("/v1/simulate", json={"shots": 128, "seed": 7})
        invalid = client.post("/v1/simulate", json={"shots": 0})
    operation = spec["paths"]["/v1/simulate"]["post"]
    for status, payload in [("200", response.json()), ("422", invalid.json())]:
        schema = {
            **operation["responses"][status]["content"]["application/json"]["schema"],
            "components": spec["components"],
        }
        Draft202012Validator(schema).validate(payload)
