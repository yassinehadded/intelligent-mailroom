from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    subject: str | None = None
    destination_entity_id: str | None = None
    destination_serial_id: int | None = None
    doctype_id: int | None = None
    doctype_label: str | None = None
    method: str
    reasoning: str | None = None


class DocumentAnalysisResult(BaseModel):
    ocr_source: str
    extracted_text_preview: str
    classification: ClassificationResult
