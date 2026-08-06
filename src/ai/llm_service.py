from __future__ import annotations

import json
import re
import requests

from src.ai.models import LLMAnalysisResult
from src.config import Settings, get_settings
from src.utils import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an AI document classifier for an Intelligent Mailroom system (Courrier Entrant / GEC).
Analyze the input text and extract metadata in STRICT JSON format ONLY.

Departments mapping:
- "FIN": Financial / Invoices / Billing / Accounting / Taxes (Factures, devis, comptabilité, TVA)
- "DRH": Human Resources / Recruitment / Payroll / Leave (RH, recrutement, congés, salaires)
- "PJU": Legal / Disputes / Appeals / Contracts / Claims (Juridique, contentieux, plaintes, contrats)
- "DSI": IT / Software / Hardware / Network / Infrastructure (Informatique, serveurs, logiciels)
- "PTE": Technical Services / Works / Urban Planning / Roads (Travaux, voirie, urbanisme, intervention)
- "PSO": Social Services / Housing / Assistance (Social, logement, aide, CCAS)
- "COU": General Mail / Uncategorized (Courrier général, autre)

You MUST respond with valid JSON containing ONLY these exact keys:
{
  "document_type": "invoice|hr_request|legal_claim|it_request|work_request|social_aid|general_mail",
  "department": "FIN|DRH|PJU|DSI|PTE|PSO|COU",
  "priority": "high|normal|low",
  "confidential": false,
  "confidence": 0.95,
  "reason": "Brief explanation in English or French"
}
Do NOT wrap the JSON in Markdown code fences if possible, or use standard ```json ... ```. No extra text before or after.
"""


class OllamaLLMService:
    """Service to interact with Qwen 2.5 7B running locally via Ollama HTTP API."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def analyze(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> LLMAnalysisResult:
        """Sends document text to Qwen via local Ollama API and returns structured LLMAnalysisResult."""
        prompt_content = f"Subject: {subject}\nSender: {sender or 'Unknown'}\nDocument Content:\n{body_text[:4000]}"

        base_url = self.settings.ollama_base_url.rstrip("/")
        chat_url = f"{base_url}/api/chat"

        payload = {
            "model": self.settings.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            response = requests.post(
                chat_url,
                json=payload,
                timeout=self.settings.ollama_timeout,
            )
            response.raise_for_status()
            data = response.json()
            raw_content = data.get("message", {}).get("content", "")
            return self._parse_response(raw_content)
        except Exception as exc:
            logger.warning("Ollama local LLM call failed or timed out: %s", exc)
            return LLMAnalysisResult(
                document_type="general_mail",
                department="COU",
                priority="normal",
                confidential=False,
                confidence=0.0,
                reason=f"Ollama API call error: {exc}",
            )

    def _parse_response(self, raw_text: str) -> LLMAnalysisResult:
        cleaned = raw_text.strip()

        # Extract JSON if enclosed in markdown backticks or extra text
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        else:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0).strip()

        try:
            parsed = json.loads(cleaned)
            dept = str(parsed.get("department", "COU")).upper()
            if dept not in {"FIN", "DRH", "PJU", "DSI", "PTE", "PSO", "COU"}:
                dept = "COU"

            conf = float(parsed.get("confidence", 0.70))
            conf = max(0.0, min(1.0, conf))

            doc_type = str(parsed.get("document_type", "general_mail"))
            priority = str(parsed.get("priority", "normal")).lower()
            confidential = bool(parsed.get("confidential", False))
            reason = str(parsed.get("reason", ""))

            return LLMAnalysisResult(
                document_type=doc_type,
                department=dept,
                priority=priority,
                confidential=confidential,
                confidence=conf,
                reason=reason,
            )
        except Exception as exc:
            logger.warning("Failed to parse JSON from Qwen response: %s (raw text: %r)", exc, raw_text[:200])
            return LLMAnalysisResult(
                document_type="general_mail",
                department="COU",
                priority="normal",
                confidential=False,
                confidence=0.0,
                reason=f"Failed to parse LLM JSON output: {exc}",
            )
