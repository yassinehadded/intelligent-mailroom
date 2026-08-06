from typing import Any
from pydantic import BaseModel, Field


class RuleAnalysisResult(BaseModel):
    department: str
    document_type: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    matched_keywords: list[str] = Field(default_factory=list)
    has_deterministic_evidence: bool = False
    evidence_details: list[str] = Field(default_factory=list)


class LLMAnalysisResult(BaseModel):
    document_type: str = ""
    department: str = ""
    priority: str = "normal"
    confidential: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reason: str = ""


class DecisionResult(BaseModel):
    department: str
    document_type: str
    priority: str = "normal"
    confidential: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    action: str = "AUTO_ACCEPT"  # "AUTO_ACCEPT" or "MANUAL_REVIEW"
    reason: str = ""
    case_applied: str = ""


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
    action: str = "AUTO_ACCEPT"
    rule_result: RuleAnalysisResult | None = None
    llm_result: LLMAnalysisResult | None = None
    decision: DecisionResult | None = None


class DocumentAnalysisResult(BaseModel):
    ocr_source: str
    extracted_text_preview: str
    classification: ClassificationResult
    ocr_text: str | None = None
    rule_result: RuleAnalysisResult | None = None
    llm_result: LLMAnalysisResult | None = None
    decision_result: DecisionResult | None = None
    processing_time_ms: float = 0.0
