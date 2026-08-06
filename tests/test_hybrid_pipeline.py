from unittest.mock import MagicMock, patch
import pytest

from src.ai.decision_engine import DecisionEngine
from src.ai.llm_service import OllamaLLMService
from src.ai.models import LLMAnalysisResult, RuleAnalysisResult
from src.ai.pipeline import DocumentAnalysisPipeline
from src.ai.rule_engine import EnhancedRuleClassifier
from src.ai.text_normalizer import normalize_arabic, remove_french_diacritics, normalize_text
from src.config import Settings
from src.database.audit import AuditRepository


def test_text_normalizer_french_diacritics():
    text = "Fiche de paie & congés payés de l'été"
    cleaned = remove_french_diacritics(text)
    assert cleaned == "Fiche de paie & conges payes de l'ete"


def test_text_normalizer_arabic():
    text = "إشعارُ بِدَفْعِ الفَاتُورَةِ، رقم 123؟"
    cleaned = normalize_arabic(text)
    assert "اشعار" in cleaned
    assert "بدفع" in cleaned
    assert "الفاتوره" in cleaned  # teh marbuta converted to heh in lowercased/normalized
    assert "؟" not in cleaned


def test_rule_engine_french_invoice():
    classifier = EnhancedRuleClassifier()
    res = classifier.analyze(
        subject="Facture prestation janvier",
        body_text="Veuillez régler la facture FAC-2026-001 montant TTC avec TVA.",
    )
    assert res.department == "FIN"
    assert res.has_deterministic_evidence is True
    assert any("FAC-2026-001" in ev for ev in res.evidence_details)


def test_rule_engine_arabic_invoice():
    classifier = EnhancedRuleClassifier()
    res = classifier.analyze(
        subject="فاتورة الخدمات",
        body_text="نرجو تسديد فاتورة رقم 45892 في أقرب وقت.",
    )
    assert res.department == "FIN"
    assert res.has_deterministic_evidence is True


def test_rule_engine_arabic_hr():
    classifier = EnhancedRuleClassifier()
    res = classifier.analyze(
        subject="طلب توظيف",
        body_text="أتقدم بسيرتي الذاتية لطلب عمل في قسم الموارد البشرية.",
    )
    assert res.department == "DRH"


def test_rule_engine_arabic_legal():
    classifier = EnhancedRuleClassifier()
    res = classifier.analyze(
        subject="دعوى قضائية",
        body_text="إحالة ملف قضية رقم 789/2026 إلى المحكمة.",
    )
    assert res.department == "PJU"
    assert res.has_deterministic_evidence is True


def test_decision_engine_case_1_agreement():
    engine = DecisionEngine()
    rule_res = RuleAnalysisResult(
        department="FIN", document_type="invoice", confidence=0.90, matched_keywords=["facture"]
    )
    llm_res = LLMAnalysisResult(
        department="FIN", document_type="invoice", confidence=0.85, reason="Matches invoice details"
    )

    dec = engine.evaluate(rule_res, llm_res)
    assert dec.action == "AUTO_ACCEPT"
    assert dec.case_applied == "CASE_1_AGREEMENT"
    assert dec.confidence == 1.0  # max(0.90, 0.85) + 0.10 capped at 1.0


def test_decision_engine_case_2_dept_mismatch():
    engine = DecisionEngine()
    rule_res = RuleAnalysisResult(
        department="DRH", document_type="hr", confidence=0.70, matched_keywords=["salaire"]
    )
    llm_res = LLMAnalysisResult(
        department="FIN", document_type="invoice", confidence=0.82, reason="Mentions payment details"
    )

    dec = engine.evaluate(rule_res, llm_res)
    assert dec.case_applied == "CASE_2_DEPT_MISMATCH"
    assert dec.department == "FIN"  # LLM had higher confidence 0.82 > 0.70


def test_decision_engine_case_3_high_llm_confidence():
    engine = DecisionEngine()
    rule_res = RuleAnalysisResult(
        department="COU", document_type="general", confidence=0.45, matched_keywords=[]
    )
    llm_res = LLMAnalysisResult(
        department="PTE", document_type="work_request", confidence=0.92, reason="Clear roadwork mention"
    )

    dec = engine.evaluate(rule_res, llm_res)
    assert dec.action == "AUTO_ACCEPT"
    assert dec.case_applied == "CASE_3_HIGH_CONF_LLM"
    assert dec.department == "PTE"


def test_decision_engine_case_4_deterministic_override():
    engine = DecisionEngine()
    rule_res = RuleAnalysisResult(
        department="FIN",
        document_type="invoice",
        confidence=0.95,
        matched_keywords=["facture"],
        has_deterministic_evidence=True,
        evidence_details=["FAC-2026-999"],
    )
    llm_res = LLMAnalysisResult(
        department="DSI", document_type="it_request", confidence=0.88, reason="Mentions software"
    )

    dec = engine.evaluate(rule_res, llm_res)
    assert dec.action == "MANUAL_REVIEW"
    assert dec.case_applied == "CASE_4_DETERMINISTIC_RULE_OVERRIDE"
    assert dec.department == "FIN"


def test_decision_engine_case_5_low_confidence():
    engine = DecisionEngine()
    rule_res = RuleAnalysisResult(
        department="COU", document_type="general", confidence=0.40, matched_keywords=[]
    )
    llm_res = LLMAnalysisResult(
        department="COU", document_type="general", confidence=0.35, reason="Unclear content"
    )

    dec = engine.evaluate(rule_res, llm_res)
    assert dec.action == "MANUAL_REVIEW"
    assert dec.case_applied == "CASE_5_LOW_CONFIDENCE"


def test_ollama_llm_service_parsing():
    settings = Settings(maarch_url="http://localhost:8081", ollama_base_url="http://localhost:11434")
    service = OllamaLLMService(settings)

    raw_response = """
    ```json
    {
      "document_type": "invoice",
      "department": "FIN",
      "priority": "high",
      "confidential": false,
      "confidence": 0.95,
      "reason": "Document is an invoice"
    }
    ```
    """
    res = service._parse_response(raw_response)
    assert res.department == "FIN"
    assert res.confidence == 0.95
    assert res.priority == "high"


def test_hybrid_pipeline_end_to_end(tmp_path):
    audit_db = str(tmp_path / "audit.db")
    settings = Settings(
        maarch_url="http://localhost:8081",
        ai_enabled=True,
        ai_provider="hybrid",
        audit_db_path=audit_db,
    )

    reference = MagicMock()
    reference.get_entity_serial_id.return_value = 17
    reference.get_flat_doctypes.return_value = [{"type_id": 407, "label": "Facture ou avoir"}]

    pipeline = DocumentAnalysisPipeline(settings=settings, reference_service=reference)

    with patch.object(pipeline.classifier.ollama_service, "analyze") as mock_ollama:
        mock_ollama.return_value = LLMAnalysisResult(
            document_type="invoice",
            department="FIN",
            priority="normal",
            confidential=False,
            confidence=0.90,
            reason="Verified invoice text",
        )

        result = pipeline.analyze(
            subject="Facture prestation 2026",
            body_text="Paiement de la facture FAC-2026-888 sous 30 jours.",
        )

    assert result.classification.destination_entity_id == "FIN"
    assert result.classification.action == "AUTO_ACCEPT"
    assert result.processing_time_ms > 0

    audit_repo = AuditRepository(settings=settings)
    audit_repo.record_event(
        event_type="test_ingested",
        subject="Facture test",
        category=result.classification.category,
        confidence=result.classification.confidence,
        ocr_text=result.ocr_text,
        rule_result=result.rule_result,
        llm_result=result.llm_result,
        final_decision=result.classification.destination_entity_id,
        decision_reason=result.classification.reasoning,
        processing_time_ms=result.processing_time_ms,
    )

    events = audit_repo.list_events(limit=5)
    assert len(events) >= 1
    assert events[0]["final_decision"] == "FIN"
    assert events[0]["rule_result"]["has_deterministic_evidence"] is True
