from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import Settings
from src.maarch.client import MaarchClient
from src.maarch.exceptions import MaarchAPIError, MaarchConfigurationError
from src.maarch.models import CreateResourceRequest


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_maarch_health_without_credentials(client):
    with patch("src.api.routes.maarch.get_maarch_service_optional", return_value=None):
        response = client.get("/api/v1/maarch/health")
    assert response.status_code == 503


def test_maarch_health_with_mocked_service():
    from src.api.routes.maarch import require_maarch_service

    mock_service = MagicMock()
    mock_service.ping.return_value = {
        "applicationName": "COURRIER DEMO",
        "authMode": "standard",
        "maarchUrl": "http://localhost:8081/",
    }

    app = create_app()
    app.dependency_overrides[require_maarch_service] = lambda: mock_service
    test_client = TestClient(app)

    response = test_client.get("/api/v1/maarch/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "connected"
    assert body["application_name"] == "COURRIER DEMO"


def test_march_client_raises_when_credentials_missing():
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username=None,
        maarch_password=None,
    )

    with pytest.raises(MaarchConfigurationError):
        MaarchClient(settings=settings)


def test_march_client_parses_api_error():
    settings = Settings(
        maarch_url="http://localhost:8081",
        maarch_username="user",
        maarch_password="pass",
    )
    maarch_client = MaarchClient(settings=settings)

    response = MagicMock()
    response.status_code = 400
    response.url = "http://localhost:8081/rest/resources"
    response.json.return_value = {"errors": "Bad Request"}
    response.content = b'{"errors":"Bad Request"}'
    response.headers = {"Content-Type": "application/json"}

    with pytest.raises(MaarchAPIError) as exc_info:
        maarch_client._parse_error_response(response)

    assert exc_info.value.status_code == 400
    assert "Bad Request" in str(exc_info.value)


def test_create_resource_request_serializes_aliases():
    payload = CreateResourceRequest(
        modelId=8,
        status="INIT",
        subject="Test courrier",
        destination=13,
    )
    dumped = payload.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert dumped["modelId"] == 8
    assert dumped["status"] == "INIT"
    assert dumped["subject"] == "Test courrier"
    assert dumped["destination"] == 13


def test_create_resource_request_serializes_dates_as_json_strings():
    payload = CreateResourceRequest(
        modelId=8,
        status="INIT",
        subject="Test courrier",
        documentDate="2026-07-30T12:20:27.764Z",
    )
    dumped = payload.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert isinstance(dumped["documentDate"], str)
    assert dumped["documentDate"].startswith("2026-07-30T12:20:27")
