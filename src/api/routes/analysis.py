from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.ai import DocumentAnalysisPipeline
from src.api.dependencies import get_maarch_service_optional
from src.config import get_settings
from src.maarch import MaarchService


router = APIRouter(prefix="/analysis", tags=["analysis"])


class ClassifyTextRequest(BaseModel):
    subject: str = Field(default="")
    body_text: str = Field(default="")
    sender: str | None = None


def require_maarch_for_analysis() -> MaarchService | None:
    return get_maarch_service_optional()


@router.get("/status")
def analysis_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "ocr_enabled": settings.ocr_enabled,
        "ocr_tesseract_enabled": settings.ocr_tesseract_enabled,
        "ai_enabled": settings.ai_enabled,
        "ai_provider": settings.ai_provider,
        "classification_min_confidence": settings.classification_min_confidence,
        "openai_configured": bool(settings.openai_api_key),
    }


@router.post("/classify")
def classify_text(
    payload: ClassifyTextRequest,
    maarch_service: MaarchService | None = Depends(require_maarch_for_analysis),
) -> dict[str, Any]:
    reference_service = maarch_service.reference if maarch_service is not None else None
    pipeline = DocumentAnalysisPipeline(reference_service=reference_service)

    try:
        result = pipeline.analyze(
            subject=payload.subject,
            sender=payload.sender,
            body_text=payload.body_text,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return result.model_dump()


@router.get("/routing-rules")
def list_routing_rules() -> dict[str, Any]:
    from src.ai.routing import ROUTING_RULES

    return {
        "rules": [
            {
                "category": rule.category,
                "entity_id": rule.entity_id,
                "keywords": list(rule.keywords),
                "doctype_keywords": list(rule.doctype_keywords),
                "default_doctype_id": rule.default_doctype_id,
            }
            for rule in ROUTING_RULES
        ]
    }
