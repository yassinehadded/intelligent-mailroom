from typing import Any

from fastapi import APIRouter, Query

from src.config import get_settings
from src.database import get_audit_repository


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=500),
    event_type: str | None = Query(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.audit_enabled:
        return {"enabled": False, "events": []}

    repository = get_audit_repository()
    events = repository.list_events(limit=limit, event_type=event_type)
    return {
        "enabled": True,
        "count": len(events),
        "events": events,
    }
