from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingRule:
    category: str
    entity_id: str
    keywords: tuple[str, ...]
    doctype_keywords: tuple[str, ...] = ()
    default_doctype_id: int | None = None


ROUTING_RULES: tuple[RoutingRule, ...] = (
    RoutingRule(
        category="invoice",
        entity_id="FIN",
        keywords=("facture", "invoice", "avoir", "paiement", "devis", "tva"),
        doctype_keywords=("facture", "avoir", "paiement"),
        default_doctype_id=407,
    ),
    RoutingRule(
        category="hr",
        entity_id="DRH",
        keywords=("rh", "human resources", "congé", "conges", "recrutement", "carrière", "personnel", "salaire"),
        doctype_keywords=("carrière", "congé", "candidature", "retraite"),
        default_doctype_id=703,
    ),
    RoutingRule(
        category="legal",
        entity_id="PJU",
        keywords=("juridique", "legal", "contentieux", "recours", "plainte", "assignation"),
        doctype_keywords=("plainte", "recours", "contentieux"),
        default_doctype_id=503,
    ),
    RoutingRule(
        category="it",
        entity_id="DSI",
        keywords=("informatique", "dsi", "it ", " serveur", "réseau", "logiciel", "cyber", "ntic"),
        doctype_keywords=("ntic",),
        default_doctype_id=911,
    ),
    RoutingRule(
        category="technical",
        entity_id="PTE",
        keywords=("voirie", "travaux", "technique", "intervention", "stationnement", "urbanisme", "encombrants"),
        doctype_keywords=("voirie", "travaux", "intervention", "stationnement"),
        default_doctype_id=1202,
    ),
    RoutingRule(
        category="social",
        entity_id="PSO",
        keywords=("social", "ccas", "aide", "logement", "rsa", "handicap"),
        doctype_keywords=("aide", "logement", "rsa"),
        default_doctype_id=801,
    ),
    RoutingRule(
        category="general",
        entity_id="COU",
        keywords=(),
        doctype_keywords=("courriel", "demande", "courrier"),
        default_doctype_id=1203,
    ),
)
