from __future__ import annotations

import io

from src.config import Settings, get_settings
from src.ocr.models import OcrResult
from src.utils import get_logger


logger = get_logger(__name__)


class DocumentTextExtractor:
    """Extracts text from documents for classification."""

    TEXT_EXTENSIONS = {"txt", "csv", "html", "htm", "xml", "json"}
    PDF_EXTENSIONS = {"pdf"}
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "gif"}

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def extract(
        self,
        *,
        content: bytes | None = None,
        extension: str | None = None,
        fallback_text: str | None = None,
    ) -> OcrResult:
        if not self.settings.ocr_enabled:
            return OcrResult(
                text=(fallback_text or "").strip(),
                source="disabled",
            )

        normalized_extension = (extension or "").lower().lstrip(".")

        if content and normalized_extension in self.TEXT_EXTENSIONS:
            text = content.decode("utf-8", errors="replace").strip()
            return OcrResult(text=text or (fallback_text or ""), source="text")

        if content and normalized_extension in self.PDF_EXTENSIONS:
            pdf_text = self._extract_pdf_text(content)
            if pdf_text.strip():
                return OcrResult(text=pdf_text.strip(), source="pdf")

        if content and normalized_extension in self.IMAGE_EXTENSIONS:
            image_text = self._extract_image_text(content)
            if image_text.strip():
                return OcrResult(text=image_text.strip(), source="ocr", confidence=0.7)

        return OcrResult(
            text=(fallback_text or "").strip(),
            source="fallback",
        )

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("pypdf is not installed; skipping PDF text extraction")
            return ""

        try:
            reader = PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except Exception as exc:
            logger.warning("PDF text extraction failed: %s", exc)
            return ""

    def _extract_image_text(self, content: bytes) -> str:
        if not self.settings.ocr_tesseract_enabled:
            return ""

        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.warning("pytesseract/Pillow not installed; skipping image OCR")
            return ""

        try:
            image = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(image, lang=self.settings.ocr_tesseract_lang)
        except Exception as exc:
            logger.warning("Image OCR failed: %s", exc)
            return ""
