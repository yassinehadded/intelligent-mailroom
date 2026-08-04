from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.api.dependencies import get_maarch_service_optional
from src.config import get_settings
from src.database import get_audit_repository


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


@router.get("/health/live")
def liveness_check() -> dict[str, str]:
    """Kubernetes/Docker liveness probe — process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness_check() -> JSONResponse:
    """
    Readiness probe — verifies dependencies required for ingestion.
    Returns 200 when ready, 503 when degraded.
    """
    settings = get_settings()
    checks: dict[str, Any] = {
        "maarch": {"status": "skipped", "detail": "not configured"},
        "email": {"status": "skipped", "detail": "not configured"},
        "audit": {"status": "skipped", "detail": "disabled"},
    }
    ready = True

    maarch_service = get_maarch_service_optional()
    if maarch_service is not None:
        try:
            connection = maarch_service.validate_connection()
            checks["maarch"] = {
                "status": "ok" if connection.get("connected") else "error",
                "webservice_ready": connection.get("webservice_ready"),
                "user": connection.get("current_user"),
                "warnings": connection.get("warnings", []),
            }
            if not connection.get("connected"):
                ready = False
        except Exception as exc:
            checks["maarch"] = {"status": "error", "detail": str(exc)}
            ready = False

    email_configured = bool(
        settings.email_host and settings.email_username and settings.email_password
    )
    if email_configured:
        checks["email"] = {"status": "configured"}
    else:
        checks["email"] = {"status": "not_configured"}

    if settings.audit_enabled:
        try:
            repository = get_audit_repository()
            repository.list_events(limit=1)
            checks["audit"] = {"status": "ok", "path": settings.audit_db_path}
        except Exception as exc:
            checks["audit"] = {"status": "error", "detail": str(exc)}
            ready = False

    payload = {
        "status": "ready" if ready else "degraded",
        "environment": settings.app_env,
        "checks": checks,
    }
    status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=payload, status_code=status_code)
