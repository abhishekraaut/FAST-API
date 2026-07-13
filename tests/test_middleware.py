from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_cors_middleware_headers(client: TestClient) -> None:
    # Send request with Origin header to verify CORS response headers
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Preflight preflight options check
    preflight_headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    preflight_response = client.options("/health", headers=preflight_headers)
    assert preflight_response.status_code == 200
    assert preflight_response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "POST" in preflight_response.headers.get("access-control-allow-methods", "")
