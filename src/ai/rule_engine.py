from __future__ import annotations

import re
from dataclasses import dataclass

from src.ai.models import RuleAnalysisResult
from src.ai.text_normalizer import normalize_text
from src.maarch.reference import ReferenceDataService
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class CategorizedRule:
    category: str  # e.g. "invoice", "hr", "legal", "it", "technical", "social", "general"
    department: str  # e.g. "FIN", "DRH", "PJU", "DSI", "PTE", "PSO", "COU"
    default_doctype_id: int | None
    doctype_label: str
    keywords_fr: tuple[str, ...] = ()
    keywords_en: tuple[str, ...] = ()
    keywords_ar: tuple[str, ...] = ()
    regex_patterns: tuple[str, ...] = ()
    deterministic_regexes: tuple[str, ...] = ()


# Department & Category Rules Definition
RULE_DEFINITIONS: tuple[CategorizedRule, ...] = (
    CategorizedRule(
        category="invoice",
        department="FIN",
        default_doctype_id=407,
        doctype_label="Facture ou avoir",
        keywords_fr=(
            "facture", "avoir", "devis", "paiement", "tva", "bon de commande",
            "comptabilite", "virement", "reglement", "honoraires", "montant ttc", "quittance"
        ),
        keywords_en=(
            "invoice", "billing", "payment", "vat", "purchase order", "tax",
            "receipt", "credit note", "quote", "remittance", "fee"
        ),
        keywords_ar=(
            "فاتورة", "فاتوره", "تسديد", "دفع", "مبلغ", "ضريبة", "كمبيالة", "وصل",
            "محاسبة", "مستحقات", "إيصال", "ايصال", "حساب", "رصيد", "سند"
        ),
        regex_patterns=(
            r"\b(facture|invoice|devis|tva|b\.c\.|bon de commande)\b",
            r"\b(مبلغ|فاتورة|ضريبة|ايصال)\b",
        ),
        deterministic_regexes=(
            r"(?i)\b(?:fac|facture|inv|invoice|avoir)[-_\s#\u2116]*[0-9][0-9A-Z_-]{2,}\b",
            r"(?i)\b(?:tva|siret|siren|ice)[-_\s:]*[0-9][0-9A-Z]{8,13}\b",
            r"\b(?:فاتورة|فاتوره|وصل)\s*(?:رقم|عدد)?\s*[:#-]?\s*[0-9][0-9A-Z_-]{2,}\b",
            r"\bالرقم\s+الضريبي\s*[:#-]?\s*[0-9]{5,}\b",
        ),
    ),
    CategorizedRule(
        category="hr",
        department="DRH",
        default_doctype_id=703,
        doctype_label="Candidature / Congés / RH",
        keywords_fr=(
            "recrutement", "candidature", "conge", "conges", "paie", "fiche de paie",
            "salaire", "personnel", "ressources humaines", "rh", "carriere",
            "arret de travail", "retraite", "embauche", "demission", "cv", "lettre de motivation"
        ),
        keywords_en=(
            "human resources", "hr", "recruitment", "leave", "payroll", "salary",
            "resume", "cv", "job application", "career", "sick leave", "retirement"
        ),
        keywords_ar=(
            "الموارد البشرية", "شؤون الموظفين", "توظيف", "ترقية", "عطلة", "اجازة",
            "إجازة", "سيرة ذاتية", "راتب", "أجر", "استقالة", "طلب عمل", "سيرة ذاتيه",
            "تقاعد", "شهادة عمل", "انتقال"
        ),
        regex_patterns=(
            r"\b(recrutement|candidature|conge|salaire|cv|rh)\b",
            r"\b(توظيف|سيرة ذاتية|الموارد البشرية|اجازة|عطلة)\b",
        ),
        deterministic_regexes=(
            r"(?i)\b(?:cv|curriculum vitae|lettre de motivation)\b",
            r"\bطلب\s+(?:توظيف|عمل|إجازة|عطلة)\b",
            r"\bسيرة\s+ذاتية\b",
        ),
    ),
    CategorizedRule(
        category="legal",
        department="PJU",
        default_doctype_id=503,
        doctype_label="Contentieux / Juridique / Plainte",
        keywords_fr=(
            "juridique", "contentieux", "plainte", "assignation", "recours",
            "tribunal", "avocat", "huissier", "jugement", "mise en demeure",
            "litige", "tribunal administratif", "decret", "arrete", "juridiction"
        ),
        keywords_en=(
            "legal", "lawsuit", "court", "litigation", "claim", "attorney",
            "lawyer", "complaint", "summons", "judgment", "decree", "appeal"
        ),
        keywords_ar=(
            "الشؤون القانونية", "قانوني", "دعوى", "شكوى", "محكمة", "محامي",
            "نزاع", "إنذار", "انذار", "طعن", "قضية", "قرار قضائي", "مرسوم",
            "مقال افتتاحي", "استدعاء", "عريضة"
        ),
        regex_patterns=(
            r"\b(contentieux|plainte|assignation|recours|mise en demeure)\b",
            r"\b(دعوى|شكوى|نزاع|محكمة|طعن)\b",
        ),
        deterministic_regexes=(
            r"(?i)\b(?:mise en demeure|tribunal administratif|assignation)\b",
            r"(?i)\b(?:decret|arrete)\s+(?:n°|no|number)?\s*[0-9]{2,}\b",
            r"\b(?:دعوى|قضية|ملف)\s*(?:رقم|عدد)\s*[:#-]?\s*[0-9/]{3,}\b",
            r"\b(?:مرسوم|قرار|قانون)\s*(?:رقم|عدد)\s*[:#-]?\s*[0-9/]{2,}\b",
        ),
    ),
    CategorizedRule(
        category="it",
        department="DSI",
        default_doctype_id=911,
        doctype_label="Demande IT / NTIC",
        keywords_fr=(
            "informatique", "dsi", "serveur", "reseau", "logiciel", "materiel",
            "ordinateur", "cybersecurite", "mot de passe", "maintenance informatique",
            "pantheon", "ntic", "licence", "assistance informatique"
        ),
        keywords_en=(
            "information technology", "it support", "server", "network", "software",
            "hardware", "computer", "cybersecurity", "password", "helpdesk"
        ),
        keywords_ar=(
            "تكنولوجيا المعلومات", "معلوميات", "خادم", "شبكة", "برمجيات", "حاسوب",
            "كمبيوتر", "صيانة معلوميات", "أمن سيبراني", "برنامج", "حساب مستخدم"
        ),
        regex_patterns=(
            r"\b(dsi|informatique|serveur|reseau|helpdesk)\b",
            r"\b(معلوميات|برمجيات|شبكة|خادم)\b",
        ),
        deterministic_regexes=(
            r"(?i)\bticket[-_\s#]*[0-9]{4,}\b",
            r"\bتذكرة\s*(?:رقم|صيانة)\s*[:#-]?\s*[0-9]{3,}\b",
        ),
    ),
    CategorizedRule(
        category="technical",
        department="PTE",
        default_doctype_id=1202,
        doctype_label="Intervention voirie / Travaux",
        keywords_fr=(
            "voirie", "travaux", "technique", "intervention", "stationnement",
            "urbanisme", "encombrants", "signalisation", "eclairage public",
            "permis de construire", "permis d'amenager", "route", "trottoir"
        ),
        keywords_en=(
            "technical services", "public works", "roads", "maintenance",
            "parking", "urban planning", "construction permit", "lighting"
        ),
        keywords_ar=(
            "الأشغال العمومية", "اشغال", "أشغال", "صيانة", "طرقات", "ترخيص بناء",
            "إنارة عمومية", "بيئة", "نظافة", "رخصة بناء", "تعمير", "إشارة مرور"
        ),
        regex_patterns=(
            r"\b(voirie|travaux|urbanisme|stationnement)\b",
            r"\b(أشغال|اشغال|طرقات|تعمير|ترخيص بناء)\b",
        ),
        deterministic_regexes=(
            r"(?i)\bpermis\s+de\s+(?:construire|demolir|amenager)\b",
            r"\bرخصة\s+(?:بناء|تعديل|تعمير)\b",
        ),
    ),
    CategorizedRule(
        category="social",
        department="PSO",
        default_doctype_id=801,
        doctype_label="Aide sociale / CCAS / Logement",
        keywords_fr=(
            "social", "ccas", "aide sociale", "logement", "rsa", "handicap",
            "allocation", "famille", "solidarite", "subvention sociale"
        ),
        keywords_en=(
            "social services", "social aid", "housing", "welfare", "disability",
            "family allowance", "grant"
        ),
        keywords_ar=(
            "الشؤون الاجتماعية", "مساعدة اجتماعية", "سكن", "إعاقة", "اعاقة",
            "تضامن", "دعم الاجتماعي", "دعم مالك", "تغطية صحية", "أسرة"
        ),
        regex_patterns=(
            r"\b(ccas|aide sociale|logement|rsa|handicap)\b",
            r"\b(مساعدة اجتماعية|سكن|تضامن|اعاقة)\b",
        ),
        deterministic_regexes=(
            r"(?i)\bdossier\s+ccas\b",
            r"\bطلب\s+مساعدة\s+اجتماعية\b",
        ),
    ),
    CategorizedRule(
        category="general",
        department="COU",
        default_doctype_id=1203,
        doctype_label="Courrier général / Non classé",
        keywords_fr=("courrier", "demande", "courriel", "information"),
        keywords_en=("mail", "inquiry", "general", "request"),
        keywords_ar=("طلب", "رسالة", "استفسار", "معلومات"),
        regex_patterns=(),
        deterministic_regexes=(),
    ),
)


class EnhancedRuleClassifier:
    """Refactored Rule-Based Classifier supporting French, English, Arabic, diacritics removal & deterministic regexes."""

    def __init__(self, reference_service: ReferenceDataService | None = None):
        self.reference_service = reference_service

    def analyze(
        self,
        *,
        subject: str,
        body_text: str,
        sender: str | None = None,
    ) -> RuleAnalysisResult:
        raw_combined = " ".join(part for part in [subject, body_text, sender or ""] if part)
        normalized_combined = normalize_text(raw_combined)

        matched_rule = None
        highest_score = 0.0
        best_matched_keywords: list[str] = []
        has_deterministic_evidence = False
        evidence_details: list[str] = []

        # Check rules
        for rule in RULE_DEFINITIONS:
            if rule.category == "general":
                continue

            score = 0.0
            matched_kw: list[str] = []
            det_evidence: list[str] = []

            # 1. Deterministic evidence search (regexes against raw and normalized text)
            for det_regex in rule.deterministic_regexes:
                matches = re.findall(det_regex, raw_combined) or re.findall(det_regex, normalized_combined)
                if matches:
                    match_val = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    det_evidence.append(f"Matched deterministic regex '{det_regex}': {match_val}")
                    score += 5.0  # High score boost

            # 2. Category keyword matching (FR, EN, AR)
            all_keywords = rule.keywords_fr + rule.keywords_en + rule.keywords_ar
            for kw in all_keywords:
                norm_kw = normalize_text(kw)
                if norm_kw and norm_kw in normalized_combined:
                    matched_kw.append(kw)
                    score += 1.0

            # 3. Regex pattern matching
            for pattern in rule.regex_patterns:
                if re.search(pattern, normalized_combined):
                    score += 1.5

            if score > highest_score:
                highest_score = score
                matched_rule = rule
                best_matched_keywords = matched_kw
                if det_evidence:
                    has_deterministic_evidence = True
                    evidence_details = det_evidence
                else:
                    has_deterministic_evidence = False
                    evidence_details = []

        if matched_rule is None or highest_score == 0.0:
            matched_rule = RULE_DEFINITIONS[-1]  # general/COU
            confidence = 0.40
        else:
            if has_deterministic_evidence:
                confidence = 0.95
            elif highest_score >= 4.0:
                confidence = 0.90
            elif highest_score >= 2.0:
                confidence = 0.80
            else:
                confidence = 0.65

        # Resolve doctype label
        doctype_label = matched_rule.doctype_label
        if self.reference_service is not None and matched_rule.default_doctype_id is not None:
            doctypes = self.reference_service.get_flat_doctypes()
            for dt in doctypes:
                if dt.get("type_id") == matched_rule.default_doctype_id:
                    doctype_label = dt.get("label", doctype_label)
                    break

        return RuleAnalysisResult(
            department=matched_rule.department,
            document_type=matched_rule.category,
            confidence=confidence,
            matched_keywords=best_matched_keywords,
            has_deterministic_evidence=has_deterministic_evidence,
            evidence_details=evidence_details,
        )
