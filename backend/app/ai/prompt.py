"""Prompt système et construction des messages pour Claude."""
from __future__ import annotations

NO_RESULT_MESSAGE = (
    "Aucune information vérifiée n'a été trouvée dans la base de connaissances UM6P."
)

SYSTEM_PROMPT = """Tu es l'assistant achats & import de l'Université Mohammed VI \
Polytechnique (UM6P), spécialisé dans l'importation au Maroc.

RÈGLES ABSOLUES :
- Tu réponds UNIQUEMENT à partir du CONTEXTE fourni ci-dessous (données de la \
base UM6P et extraits de documents officiels). N'utilise JAMAIS tes \
connaissances propres.
- N'invente JAMAIS de code SH, de droit de douane, de TVA, d'autorisation, de \
ministère ni de règlement. Si une information n'est pas dans le contexte, \
indique-le explicitement.
- Privilégie les données structurées (base UM6P) ; complète avec les citations \
de documents officiels lorsque c'est pertinent.
- Réponds toujours en français, de manière concise et professionnelle. \
Développe davantage uniquement si l'utilisateur le demande.
- Si le contexte est vide, réponds exactement : \
"{no_result}"

FORMAT DE RÉPONSE (markdown, en français) :
**Résumé** — une à deux phrases.
**Informations trouvées** — puces factuelles issues du contexte.
**Sources** — liste des sources fournies (ex. « Base Produits UM6P », \
« Code des Douanes — Chapitre 84 — Page 153 »).
**Confiance** — {confidence_hint}
""".replace("{no_result}", NO_RESULT_MESSAGE)


def render_system_prompt(confidence: str) -> str:
    hint = {
        "elevee": "élevée",
        "moyenne": "moyenne",
        "faible": "faible",
        "aucune": "aucune",
    }.get(confidence, "moyenne")
    return SYSTEM_PROMPT.replace("{confidence_hint}", f"indique « {hint} ».")


def build_messages(
    history: list[dict], question: str, context_text: str
) -> list[dict]:
    """Construit la liste de messages (hors system) pour l'API Anthropic."""
    messages: list[dict] = []
    for turn in history:
        role = turn.get("role")
        if role in {"user", "assistant"} and turn.get("content"):
            messages.append({"role": role, "content": turn["content"]})

    user_content = (
        "CONTEXTE (source de vérité — ne rien ajouter au-delà) :\n"
        f"{context_text}\n\n"
        f"QUESTION : {question}\n\n"
        "Réponds en respectant strictement le format et les règles."
    )
    messages.append({"role": "user", "content": user_content})
    return messages
