import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.mark.parametrize("path", ["/health", "/v1/health"])
def test_health(path: str) -> None:
    with TestClient(app) as client:
        response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_versioned_openapi() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/v1/health" in response.json()["paths"]
    assert "/health" not in response.json()["paths"]
