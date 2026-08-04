from pydantic import BaseModel, Field


class OcrResult(BaseModel):
    text: str
    source: str
    page_count: int = 1
    confidence: float | None = None
