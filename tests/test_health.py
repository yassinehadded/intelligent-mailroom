from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import Settings


def test_liveness_endpoint():
    client = TestClient(create_app())
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_endpoint_when_maarch_unavailable():
    client = TestClient(create_app())

    with patch("src.api.routes.health.get_maarch_service_optional", return_value=None):
        with patch("src.api.routes.health.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                maarch_url="http://localhost:8081",
                audit_enabled=False,
                email_host=None,
            )
            response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["maarch"]["status"] == "skipped"


def test_readiness_endpoint_degraded_when_maarch_fails():
    client = TestClient(create_app())

    mock_maarch = MagicMock()
    mock_maarch.validate_connection.side_effect = RuntimeError("connection refused")

    with patch("src.api.routes.health.get_maarch_service_optional", return_value=mock_maarch):
        with patch("src.api.routes.health.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                maarch_url="http://localhost:8081",
                maarch_username="user",
                maarch_password="pass",
                audit_enabled=False,
            )
            response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
