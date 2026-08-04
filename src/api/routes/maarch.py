from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_maarch_service_optional
from src.maarch import (
    CreateAttachmentRequest,
    CreateResourceRequest,
    MaarchAPIError,
    MaarchService,
    ResourceListQuery,
)
from src.config import get_settings


router = APIRouter(prefix="/maarch", tags=["maarch"])


def require_maarch_service() -> MaarchService:
    service = get_maarch_service_optional()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maarch credentials are not configured",
        )
    return service


@router.get("/connection")
def maarch_connection(service: MaarchService = Depends(require_maarch_service)) -> dict[str, Any]:
    try:
        return service.validate_connection()
    except MaarchAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/health")
def maarch_health(service: MaarchService = Depends(require_maarch_service)) -> dict[str, Any]:
    try:
        info = service.ping()
    except MaarchAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "status": "connected",
        "application_name": info.get("applicationName"),
        "auth_mode": info.get("authMode"),
        "maarch_url": info.get("maarchUrl"),
    }


@router.get("/entities")
def list_entities(service: MaarchService = Depends(require_maarch_service)) -> dict[str, Any]:
    entities = service.reference.get_entities()
    return {
        "count": len(entities),
        "entities": [entity.model_dump(by_alias=True) for entity in entities],
    }


@router.get("/reference")
def reference_summary(service: MaarchService = Depends(require_maarch_service)) -> dict[str, Any]:
    settings = get_settings()
    return {
        "indexing_models": [
            model.model_dump(by_alias=True)
            for model in service.reference.get_indexing_models()
        ],
        "statuses": service.reference.get_statuses(),
        "priorities": service.reference.get_priorities(),
        "defaults": {
            "model_id": settings.maarch_default_model_id,
            "status": settings.maarch_default_status,
            "attachment_type": settings.maarch_default_attachment_type,
            "priority": service.reference.get_default_priority_id(),
        },
    }


@router.post("/resources", status_code=status.HTTP_201_CREATED)
def create_resource(
    payload: CreateResourceRequest,
    service: MaarchService = Depends(require_maarch_service),
) -> dict[str, int]:
    try:
        result = service.resources.create(payload)
    except MaarchAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {"res_id": result.res_id}


@router.post("/resources/search")
def search_resources(
    query: ResourceListQuery,
    service: MaarchService = Depends(require_maarch_service),
) -> dict[str, Any]:
    try:
        return service.resources.list(query)
    except MaarchAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/attachments", status_code=status.HTTP_201_CREATED)
def create_attachment(
    payload: CreateAttachmentRequest,
    service: MaarchService = Depends(require_maarch_service),
) -> dict[str, int]:
    try:
        result = service.attachments.create(payload)
    except MaarchAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {"id": result.id}
