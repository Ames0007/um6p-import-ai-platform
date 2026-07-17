"""Couche de compréhension du langage (Claude) — étape 1 du pipeline.

Claude reçoit UNIQUEMENT la question de l'utilisateur et renvoie UNIQUEMENT
un JSON structuré (intention, langue, entités, requête normalisée). Il
n'interroge pas la base et ne rédige aucune réponse : son seul rôle est de
*comprendre* la langue naturelle des achats/import.

Le JSON alimente ensuite le retriever, qui ne cherche donc plus jamais la
phrase brute mais uniquement `normalized_query` et les entités extraites.

Robustesse : si le client Claude est indisponible (pas de clé API) ou renvoie
un JSON invalide, on bascule sur une extraction déterministe équivalente afin
que le système reste opérationnel et produise le même contrat JSON.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field

from app.ai.claude_client import claude_client
from app.ai.intents import Intent

# --- Vocabulaire d'intentions supporté (contrat JSON) ---
SUPPORTED_INTENTS = {
    "hs_lookup",
    "tax_lookup",
    "authorization_lookup",
    "product_lookup",
    "supplier_lookup",
    "purchase_history",
    "document_lookup",
    "invoice_analysis",
    "general_question",
    "comparison",
}

# Correspondance vers l'énum interne consommée par le retriever/pipeline
# (on ne redéfinit PAS l'énum : on réutilise l'existant).
_INTENT_TO_ENUM: dict[str, Intent] = {
    "hs_lookup": Intent.HS_CODE,
    "tax_lookup": Intent.TAX,
    "authorization_lookup": Intent.AUTHORIZATION,
    "product_lookup": Intent.PRODUCT_SEARCH,
    "supplier_lookup": Intent.SUPPLIER,
    "purchase_history": Intent.PURCHASE_HISTORY,
    "document_lookup": Intent.DOCUMENT_SEARCH,
    "invoice_analysis": Intent.INVOICE_ANALYSIS,
    "general_question": Intent.GENERAL_PROCUREMENT,
    "comparison": Intent.GENERAL_PROCUREMENT,
    # alias tolérés côté Claude
    "import_information": Intent.PRODUCT_SEARCH,
    "unknown": Intent.GENERAL_PROCUREMENT,
}

# Familles d'entités reconnues (toutes optionnelles, listes vides par défaut).
ENTITY_KEYS = (
    "products",
    "hs_codes",
    "chemicals",
    "commercial_names",
    "scientific_names",
    "countries",
    "suppliers",
    "manufacturers",
    "organizations",
    "standards",
    "certificates",
    "customs_chapters",
    "documents",
)

_STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "l", "d", "en", "et", "ou", "un",
    "une", "pour", "avec", "sur", "au", "aux", "nous", "je", "vous", "the",
}


def _fold(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


@dataclass
class QueryPlan:
    """Sortie de la compréhension : contrat JSON structuré."""

    intent: str = "general_question"
    language: str = "fr"
    normalized_query: str = ""
    entities: dict[str, list[str]] = field(default_factory=dict)
    source: str = "heuristic"  # "claude" | "heuristic"

    def mapped_intent(self) -> Intent:
        return _INTENT_TO_ENUM.get(self.intent, Intent.GENERAL_PROCUREMENT)

    def ents(self, key: str) -> list[str]:
        return [e for e in self.entities.get(key, []) if e]

    def to_json(self) -> dict:
        return {
            "intent": self.intent,
            "language": self.language,
            "normalized_query": self.normalized_query,
            "entities": {k: self.entities.get(k, []) for k in ENTITY_KEYS},
        }

    def search_terms(self) -> list[str]:
        """Termes que le retriever doit chercher (jamais la phrase brute).

        Ordre : codes SH explicites → requête normalisée → entités produit/
        chimique/commerciale/scientifique → chapitre douanier → mots-clés
        discriminants (repli pour une catégorie large). Dédupliqué, sans vide.
        """
        terms: list[str] = []
        terms += self.ents("hs_codes")
        if self.normalized_query:
            terms.append(self.normalized_query)
        for key in ("products", "chemicals", "commercial_names", "scientific_names"):
            terms += self.ents(key)
        terms += [f"chapitre {c}" for c in self.ents("customs_chapters")]
        # Repli : mots-clés discriminants (les plus longs d'abord).
        tokens = [
            t for t in re.split(r"[^0-9A-Za-zÀ-ÿ]+", self.normalized_query)
            if len(t) >= 4 and _fold(t) not in _STOPWORDS
        ]
        terms += sorted(set(tokens), key=len, reverse=True)

        seen: set[str] = set()
        ordered: list[str] = []
        for t in terms:
            t = (t or "").strip()
            key = _fold(t)
            if t and key not in seen:
                seen.add(key)
                ordered.append(t)
        return ordered


# --- Extraction déterministe (repli, contrat identique à Claude) ---
_HS_RE = re.compile(r"(?<!\d)(\d{4}\.\d{2}(?:\.\d{2}){0,2}|\d{2}\.\d{2})(?!\d)")
_CHAP_RE = re.compile(r"chapitre\s+(\d{1,3})", re.IGNORECASE)

# Amorces de phrase à retirer pour isoler l'objet de la demande.
_LEADINS = [
    r"^\s*(?:nous\s+(?:voulons|souhaitons|voudrions|aimerions|comptons)\s+)?"
    r"(?:importer|acheter|commander|acqu[eé]rir|approvisionner\s+en)\s+",
    r"^\s*je\s+(?:veux|voudrais|souhaite|compte)\s+"
    r"(?:importer|acheter|commander|acqu[eé]rir)\s+",
    r"^\s*quel(?:le)?s?\s+(?:est|sont)\s+le?s?\s+"
    r"(?:code\s*sh|position\s+tarifaire|nomenclature)\s+(?:du|de\s+la|de\s+l['’]|des|de|pour)\s+",
    r"^\s*quel(?:le)?s?\s+(?:est|sont)\s+le?s?\s+"
    r"(?:droits?\s+d['’]importation|taxes?|tva|droits?\s+de\s+douane)\s+"
    r"(?:du|de\s+la|de\s+l['’]|des|de|pour|applicables?\s+(?:au|à|a)\s*x?)\s+",
    r"^\s*quel(?:le)?s?\s+documents?\s+(?:parlent|traitent|concernent|mentionnent|portent)\s+"
    r"(?:de\s+la|de\s+l['’]|du|des|de|sur)\s+",
    r"^\s*montre[- ]?moi\s+(?:les\s+)?(?:produits?\s+)?(?:du|de\s+la|de\s+l['’]|des|de)\s+",
    r"^\s*(?:donne[- ]?moi|liste[- ]?moi|affiche[- ]?moi)\s+(?:les\s+)?"
    r"(?:produits?\s+)?(?:du|de\s+la|de\s+l['’]|des|de)\s+",
]
_LEAD_ARTICLE = re.compile(
    r"^(?:de\s+l['’]|de\s+la\b|d['’]|l['’]|du\b|des\b|de\b|les\b|le\b|la\b)\s*",
    re.IGNORECASE,
)


def _clean_query(text: str) -> str:
    q = text.strip()
    for pat in _LEADINS:
        new = re.sub(pat, "", q, flags=re.IGNORECASE)
        if new != q:
            q = new
            break
    q = _LEAD_ARTICLE.sub("", q)
    q = q.strip().rstrip("?.!;: ").strip()
    q = " ".join(q.split())
    return (q[:1].upper() + q[1:]) if q else q


def _heuristic_intent(folded: str, normalized_query: str) -> str:
    nq = normalized_query.strip()
    if re.search(r"facture|proforma", folded):
        return "invoice_analysis"
    if re.search(r"comparer|comparaison|difference\s+entre|\bversus\b|\bvs\b", folded):
        return "comparison"
    # Question de fournisseur.
    if re.search(r"fournisseur|fabricant|aupres\s+de\s+qui", folded):
        return "supplier_lookup"
    # Historique/prix (distinct de l'intention « acheter »).
    if re.search(r"\bprix\b|historique|combien|co[uû]t|\bachat\b|achet[eé]s?\b|pay[eé]", folded):
        return "purchase_history"
    if re.search(r"\bcode\s*sh\b|nomenclature|position\s+tarifaire", folded):
        return "hs_lookup"
    # Requête = uniquement un code SH.
    if _HS_RE.fullmatch(nq.replace(" ", "")):
        return "hs_lookup"
    if re.search(r"droits?\s+d|taxe|\btva\b|douan|parafiscal|quotit|taxation", folded):
        return "tax_lookup"
    if re.search(r"autorisation|licence|agrement|\bcontrole\b|permis|ministere|autorise", folded):
        return "authorization_lookup"
    if re.search(r"document|circulaire|parlent|texte\s+officiel|reglement|annexe", folded):
        return "document_lookup"
    if re.search(r"importer|acheter|commander|acqu[eé]rir|approvisionn|besoin\s+d", folded):
        return "product_lookup"
    if re.search(r"produit|article|reference", folded):
        return "product_lookup"
    return "general_question"


def _heuristic_plan(question: str) -> QueryPlan:
    folded = _fold(question)
    normalized = _clean_query(question)
    hs_codes = _HS_RE.findall(question)
    chapters = _CHAP_RE.findall(question)
    intent = _heuristic_intent(folded, normalized)

    entities: dict[str, list[str]] = {k: [] for k in ENTITY_KEYS}
    entities["hs_codes"] = list(dict.fromkeys(hs_codes))
    entities["customs_chapters"] = list(dict.fromkeys(chapters))

    # L'objet principal (hors code/chapitre) est traité comme produit + chimique.
    core = normalized
    if core and not _HS_RE.fullmatch(core.replace(" ", "")) and not _CHAP_RE.search(core):
        entities["products"] = [core]
        entities["chemicals"] = [core]

    return QueryPlan(
        intent=intent,
        language="fr",
        normalized_query=normalized,
        entities=entities,
        source="heuristic",
    )


# --- Prompt système de compréhension (JSON strict, aucune réponse) ---
_SYSTEM = """Tu es un analyseur de langage pour un copilote achats & import (UM6P, Maroc).

Ton UNIQUE rôle est de COMPRENDRE la question de l'utilisateur. Tu ne réponds \
JAMAIS à la question, tu n'interroges AUCUNE base, tu n'expliques rien.

Tu renvoies EXCLUSIVEMENT un objet JSON valide, sans texte, sans markdown, sans \
commentaire, respectant ce schéma :

{
  "intent": <une valeur parmi: hs_lookup, tax_lookup, authorization_lookup, \
product_lookup, supplier_lookup, purchase_history, document_lookup, \
invoice_analysis, general_question, comparison>,
  "language": <code langue ISO, ex: "fr", "en">,
  "normalized_query": <le terme essentiel recherché, nettoyé des formules de \
politesse et des verbes (ex: "Urée", "Chlorure de potassium", "3104.20")>,
  "entities": {
    "products": [], "hs_codes": [], "chemicals": [], "commercial_names": [], \
"scientific_names": [], "countries": [], "suppliers": [], "manufacturers": [], \
"organizations": [], "standards": [], "certificates": [], "customs_chapters": [], \
"documents": []
  }
}

Règles :
- N'invente aucune valeur : n'extrais que ce qui est présent dans la question.
- Les codes SH gardent leur format d'origine (ex: "3104.20").
- Les numéros de chapitre douanier vont dans "customs_chapters" (ex: "31").
- Ne renvoie que le JSON, rien d'autre.

Exemples :
Q: Nous voulons importer de l'urée.
{"intent":"product_lookup","language":"fr","normalized_query":"Urée","entities":{"products":["Urée"],"chemicals":["Urée"],"hs_codes":[],"commercial_names":[],"scientific_names":[],"countries":[],"suppliers":[],"manufacturers":[],"organizations":[],"standards":[],"certificates":[],"customs_chapters":[],"documents":[]}}
Q: Quel est le droit d'importation du chlorure de potassium ?
{"intent":"tax_lookup","language":"fr","normalized_query":"Chlorure de potassium","entities":{"products":["Chlorure de potassium"],"chemicals":["Chlorure de potassium"],"hs_codes":[],"commercial_names":[],"scientific_names":[],"countries":[],"suppliers":[],"manufacturers":[],"organizations":[],"standards":[],"certificates":[],"customs_chapters":[],"documents":[]}}
Q: 3104.20
{"intent":"hs_lookup","language":"fr","normalized_query":"3104.20","entities":{"hs_codes":["3104.20"],"products":[],"chemicals":[],"commercial_names":[],"scientific_names":[],"countries":[],"suppliers":[],"manufacturers":[],"organizations":[],"standards":[],"certificates":[],"customs_chapters":[],"documents":[]}}
"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json(text: str) -> dict | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = _JSON_RE.search(cleaned)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _plan_from_dict(data: dict, question: str) -> QueryPlan:
    intent = str(data.get("intent") or "").strip()
    if intent not in SUPPORTED_INTENTS and intent not in _INTENT_TO_ENUM:
        intent = "general_question"
    raw_entities = data.get("entities") or {}
    entities: dict[str, list[str]] = {k: [] for k in ENTITY_KEYS}
    for key, value in raw_entities.items():
        if key in entities:
            if isinstance(value, str):
                value = [value]
            entities[key] = [str(v).strip() for v in (value or []) if str(v).strip()]
    normalized = str(data.get("normalized_query") or "").strip() or _clean_query(question)
    language = str(data.get("language") or "fr").strip() or "fr"
    return QueryPlan(
        intent=intent,
        language=language,
        normalized_query=normalized,
        entities=entities,
        source="claude",
    )


class QueryUnderstanding:
    """Étape 1 : transformer la question en JSON structuré via Claude."""

    def understand(self, question: str) -> QueryPlan:
        if claude_client.available:
            try:
                gen = claude_client.generate(
                    _SYSTEM, [{"role": "user", "content": question.strip()}]
                )
                if gen.ok:
                    data = _parse_json(gen.text)
                    if data is not None:
                        return _plan_from_dict(data, question)
            except Exception:  # jamais bloquant : repli déterministe
                pass
        return _heuristic_plan(question)


query_understanding = QueryUnderstanding()
