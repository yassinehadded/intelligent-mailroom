from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_maarch_service_optional
from src.config import get_settings
from src.email import EmailConfigurationError, EmailConnectionError, ImapClient
from src.email.processor import EmailIngestionService
from src.maarch import MaarchService


router = APIRouter(prefix="/email", tags=["email"])


def require_email_configured() -> None:
    settings = get_settings()
    if not settings.email_host or not settings.email_username or not settings.email_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email/IMAP credentials are not configured",
        )


def require_maarch_for_ingestion() -> MaarchService:
    service = get_maarch_service_optional()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maarch credentials are not configured",
        )
    return service


@router.get("/status")
def email_status() -> dict[str, Any]:
    settings = get_settings()
    configured = bool(
        settings.email_host and settings.email_username and settings.email_password
    )
    return {
        "configured": configured,
        "host": settings.email_host,
        "mailbox": settings.email_mailbox,
        "fetch_limit": settings.email_fetch_limit,
        "default_destination": settings.email_default_destination,
        "mark_as_read": settings.email_mark_as_read,
    }


@router.get("/health")
def email_health(_: None = Depends(require_email_configured)) -> dict[str, Any]:
    try:
        return ImapClient().ping()
    except EmailConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EmailConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/poll")
def poll_mailbox(
    limit: int | None = Query(default=None, ge=1, le=100),
    _: None = Depends(require_email_configured),
    maarch_service: MaarchService = Depends(require_maarch_for_ingestion),
) -> dict[str, Any]:
    service = EmailIngestionService(maarch_service=maarch_service)

    try:
        result = service.poll_and_ingest(limit=limit)
    except EmailConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EmailConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return result.model_dump()
