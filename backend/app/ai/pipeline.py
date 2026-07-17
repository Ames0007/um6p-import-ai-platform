"""Orchestrateur du copilote IA.

Séquence : détecter l'intention → récupérer les données (PostgreSQL puis
documents) → construire le contexte → répondre. Claude n'est appelé que
lorsqu'un contexte vérifié existe ; sinon la réponse est déterministe.
"""
from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.ai.claude_client import claude_client
from app.ai.context import ContextPackage, context_builder
from app.ai.intents import INTENT_LABELS_FR, Intent
from app.ai.memory import Focus, memory
from app.ai.prompt import NO_RESULT_MESSAGE, build_messages, render_system_prompt
from app.ai.retriever import RetrievalResult, retriever
from app.ai.understanding import QueryPlan, query_understanding
from app.models.ai_request_log import AiRequestLog
from app.schemas.chat import (
    AskResponse,
    Candidate,
    DocumentCitationOut,
    Source,
)

logger = logging.getLogger("ai.pipeline")

_SQL_CAP = 30  # nb max d'instructions SQL conservées par terme (traçabilité)


@contextmanager
def _capture_sql(db: Session):
    """Enregistre les instructions SQL exécutées sur la connexion pendant le bloc."""
    statements: list[str] = []
    engine = db.get_bind()

    def _before(conn, cursor, statement, parameters, context, executemany):
        if len(statements) < _SQL_CAP:
            statements.append(" ".join(str(statement).split()))

    event.listen(engine, "before_cursor_execute", _before)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _before)

INVOICE_MESSAGE = (
    "**Résumé**\n"
    "L'analyse de factures est disponible dans le module « Analyse d'importation ».\n\n"
    "**Informations trouvées**\n"
    "- Ouvrez « Analyse d'importation » et téléversez votre facture "
    "(PDF, Excel, Word ou CSV). Le système en extrait les lignes produits, "
    "rapproche les codes SH, les taxes et les autorisations, puis produit un "
    "rapport de conformité.\n"
    "- Les factures numériques (texte) sont analysées directement ; les images "
    "et PDF scannés nécessitent l'activation de l'OCR.\n\n"
    "**Sources**\n- Module Analyse d'importation UM6P\n\n**Confiance**\nélevée"
)

# Intentions nécessitant un produit précis (⇒ demande de clarification si ambigu).
_SPECIFIC = {
    Intent.TAX,
    Intent.AUTHORIZATION,
    Intent.PURCHASE_HISTORY,
    Intent.SUPPLIER,
    Intent.HS_CODE,
}


class _Prepared:
    """Résultat des étapes communes (avant génération)."""

    def __init__(self, conversation, intent, result, context, mode, answer=None,
                 *, plan=None, retriever_query="", executed_sql=None):
        self.conversation = conversation
        self.intent: Intent = intent
        self.result: RetrievalResult = result
        self.context: ContextPackage = context
        self.mode = mode  # "invoice" | "no_result" | "selection" | "generate"
        self.answer = answer  # réponse figée pour les modes non génératifs
        self.plan: QueryPlan | None = plan
        self.retriever_query = retriever_query
        self.executed_sql = executed_sql or []


class AiPipeline:
    # -------- étapes communes --------
    def _resolve(
        self, db: Session, plan: QueryPlan, intent: Intent, focus: Focus
    ) -> tuple[RetrievalResult, str, list[dict]]:
        """Interroge le retriever à partir du JSON (normalized_query + entités).

        On essaie les termes issus de la compréhension dans l'ordre de priorité
        et on retient le premier qui ramène des données structurées, un aperçu
        chapitre ou des documents. La phrase brute n'est jamais transmise.
        """
        terms = plan.search_terms() or [plan.normalized_query]
        best: RetrievalResult | None = None
        best_query = terms[0] if terms else ""
        sql_log: list[dict] = []
        for term in terms:
            if not term:
                continue
            with _capture_sql(db) as statements:
                res = retriever.retrieve(db, intent=intent, query=term, focus=focus)
            # dédoublonne en préservant l'ordre
            uniq = list(dict.fromkeys(statements))
            sql_log.append({"term": term, "statements": uniq})
            if best is None:
                best, best_query = res, term
            if res.has_structured or res.documents or res.is_broad:
                best, best_query = res, term
                break
        if best is None:  # aucun terme exploitable
            with _capture_sql(db) as statements:
                best = retriever.retrieve(db, intent=intent, query="", focus=focus)
            sql_log.append({"term": "", "statements": list(dict.fromkeys(statements))})
        return best, best_query, sql_log

    def _prepare(self, db: Session, question: str, conversation_id) -> _Prepared:
        conversation = memory.get_or_create(db, conversation_id)
        focus = memory.current_focus(db, conversation.id)

        # Étape 1 — compréhension du langage : Claude renvoie un JSON structuré.
        # (Claude ne répond pas et n'interroge pas la base ici.)
        plan = query_understanding.understand(question)
        intent = plan.mapped_intent()

        if intent == Intent.INVOICE_ANALYSIS:
            return _Prepared(
                conversation, intent, RetrievalResult(intent=intent),
                ContextPackage(text="", confidence="aucune"),
                "invoice", INVOICE_MESSAGE,
                plan=plan, retriever_query=plan.normalized_query, executed_sql=[],
            )

        # Étape 2 — récupération pilotée UNIQUEMENT par le JSON.
        result, used_query, sql_log = self._resolve(db, plan, intent, focus)
        context = context_builder.build(result)

        trace = {"plan": plan, "retriever_query": used_query, "executed_sql": sql_log}

        # Requête large → aperçu au niveau chapitre puis invitation à préciser.
        if result.is_broad and result.chapter_codes:
            return _Prepared(
                conversation, intent, result, context, "chapter",
                self._chapter_answer(result, context), **trace,
            )

        # Ambiguïté : plusieurs produits pour une question ciblée → clarifier.
        if result.needs_selection and intent in _SPECIFIC | {Intent.PRODUCT_SEARCH}:
            answer = (
                "**Résumé**\nPlusieurs produits correspondent à votre demande.\n\n"
                "**Informations trouvées**\n"
                "- Précisez le produit concerné dans la liste ci-dessous.\n\n"
                "**Sources**\n- Base Produits UM6P\n\n**Confiance**\nfaible"
            )
            return _Prepared(
                conversation, intent, result, context, "selection", answer, **trace
            )

        if context.is_empty:
            return _Prepared(
                conversation, intent, result, context, "no_result",
                NO_RESULT_MESSAGE, **trace,
            )

        return _Prepared(conversation, intent, result, context, "generate", **trace)

    def _candidates(self, result: RetrievalResult) -> list[Candidate]:
        return [
            Candidate(
                id=str(p.id),
                label=p.name,
                sublabel=p.reference or p.brand or p.category,
            )
            for p in result.products
        ]

    def _chapter_candidates(self, result: RetrievalResult) -> list[Candidate]:
        return [
            Candidate(id=hs.code, label=hs.code, sublabel=(hs.description_fr or "")[:90])
            for hs in result.chapter_codes[:8]
        ]

    def _chapter_answer(self, result: RetrievalResult, context: ContextPackage) -> str:
        conf = {
            "elevee": "élevée", "moyenne": "moyenne",
            "faible": "faible", "aucune": "aucune",
        }[context.confidence]
        sources = "\n".join(f"- {s['label']}" for s in context.sources) or "- —"
        example = result.chapter_codes[0].code if result.chapter_codes else "un code SH"
        return (
            f"**Résumé**\n{result.chapter_name} — aperçu du référentiel douanier UM6P "
            f"({len(result.chapter_codes)} code(s) SH disponible(s)).\n\n"
            f"**Informations trouvées**\n{context.text}\n\n"
            f"**Sources**\n{sources}\n\n"
            f"**Confiance**\n{conf}\n\n"
            "**Préciser votre demande**\n"
            "Indiquez un produit précis ou un code SH "
            f"(par ex. « {example} ») pour obtenir la description exacte, les taxes, "
            "les autorisations et les détails de conformité."
        )

    def _deterministic_answer(self, prep: _Prepared) -> str:
        result, context = prep.result, prep.context
        if result.resolved_product:
            subject = f"« {result.resolved_product.name} »"
        elif result.hs_code:
            subject = f"le code SH {result.hs_code.code}"
        else:
            subject = "votre demande"
        conf = {
            "elevee": "élevée", "moyenne": "moyenne",
            "faible": "faible", "aucune": "aucune",
        }[context.confidence]
        sources = "\n".join(f"- {s['label']}" for s in context.sources) or "- —"
        return (
            f"**Résumé**\nInformations vérifiées concernant {subject}, "
            "issues de la base de connaissances UM6P.\n\n"
            f"**Informations trouvées**\n{context.text}\n\n"
            f"**Sources**\n{sources}\n\n"
            f"**Confiance**\n{conf}"
        )

    def _build_response(
        self, prep: _Prepared, answer: str
    ) -> AskResponse:
        selection = prep.mode == "selection"
        chapter = prep.mode == "chapter"
        if selection:
            candidates = self._candidates(prep.result)
        elif chapter:
            candidates = self._chapter_candidates(prep.result)
        else:
            candidates = []
        return AskResponse(
            answer=answer,
            conversation_id=prep.conversation.id,
            intent=INTENT_LABELS_FR[prep.intent],
            confidence=prep.context.confidence,
            sources=[Source(**s) for s in prep.context.sources],
            citations=[DocumentCitationOut(**c) for c in prep.context.citations],
            candidates=candidates,
            needs_clarification=selection or chapter,
        )

    def _log(
        self, db: Session, prep: _Prepared, question: str, answer: str,
        *, prompt: str | None, execution_ms: int,
        input_tokens: int = 0, output_tokens: int = 0,
        model: str | None = None, error: str | None = None,
    ) -> None:
        try:
            db.add(
                AiRequestLog(
                    conversation_id=prep.conversation.id,
                    question=question,
                    intent=prep.intent.value,
                    understanding=prep.plan.to_json() if prep.plan else None,
                    retriever_query=prep.retriever_query,
                    executed_sql={"terms": prep.executed_sql},
                    retrieved_records={
                        "product": str(prep.result.resolved_product.id)
                        if prep.result.resolved_product else None,
                        "candidates": len(prep.result.products),
                        "hs_code": prep.result.hs_code.code if prep.result.hs_code else None,
                        "taxes": len(prep.result.taxes),
                        "authorizations": len(prep.result.authorizations),
                        "purchases": len(prep.result.purchases),
                        # Index de connaissance : concepts appariés + tables chargées.
                        "knowledge_index_matches": [
                            {"type": h.type, "reference": h.reference,
                             "title": h.title, "score": h.score}
                            for h in prep.result.ki_matches
                        ],
                        "loaded_tables": prep.result.loaded_tables,
                    },
                    retrieved_documents={
                        "citations": prep.context.citations,
                    },
                    prompt=prompt,
                    response=answer,
                    confidence=prep.context.confidence,
                    execution_ms=execution_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    error=error,
                )
            )
            db.commit()
        except Exception:  # l'observabilité ne doit jamais casser la réponse
            db.rollback()
            logger.warning("Échec d'écriture du journal IA.", exc_info=True)

    # -------- variante non diffusée --------
    def ask(self, db: Session, question: str, conversation_id=None) -> AskResponse:
        start = time.perf_counter()
        prep = self._prepare(db, question, conversation_id)

        prompt_text = None
        input_tokens = output_tokens = 0
        model = error = None

        if prep.mode == "generate":
            system = render_system_prompt(prep.context.confidence)
            history = memory.history(db, prep.conversation.id)
            messages = build_messages(history, question, prep.context.text)
            prompt_text = f"[system]\n{system}\n\n[context]\n{prep.context.text}"
            fallback = self._deterministic_answer(prep)
            if claude_client.available:
                gen = claude_client.generate(system, messages)
                if gen.ok:
                    answer = gen.text
                    input_tokens, output_tokens = gen.input_tokens, gen.output_tokens
                    model, error = gen.model, gen.error
                else:
                    answer, error = fallback, gen.error
            else:
                answer = fallback
        else:
            answer = prep.answer or NO_RESULT_MESSAGE

        execution_ms = int((time.perf_counter() - start) * 1000)

        memory.save_turn(
            db, prep.conversation, question=question, answer=answer,
            sources=prep.context.sources, focus=prep.result.focus,
        )
        self._log(
            db, prep, question, answer, prompt=prompt_text,
            execution_ms=execution_ms, input_tokens=input_tokens,
            output_tokens=output_tokens, model=model, error=error,
        )
        return self._build_response(prep, answer)

    # -------- variante diffusée (SSE) --------
    def stream(self, db: Session, question: str, conversation_id=None) -> Iterator[dict]:
        start = time.perf_counter()
        prep = self._prepare(db, question, conversation_id)
        response = self._build_response(prep, answer="")

        # Événement méta d'abord (sources, confiance, candidats).
        yield {
            "type": "meta",
            "conversation_id": str(prep.conversation.id),
            "intent": response.intent,
            "confidence": response.confidence,
            "sources": [s.model_dump() for s in response.sources],
            "citations": [c.model_dump() for c in response.citations],
            "candidates": [c.model_dump() for c in response.candidates],
            "needs_clarification": response.needs_clarification,
        }

        prompt_text = None
        input_tokens = output_tokens = 0
        model = error = None
        parts: list[str] = []

        if prep.mode == "generate" and claude_client.available:
            system = render_system_prompt(prep.context.confidence)
            history = memory.history(db, prep.conversation.id)
            messages = build_messages(history, question, prep.context.text)
            prompt_text = f"[system]\n{system}\n\n[context]\n{prep.context.text}"
            streamed_ok = False
            for event in claude_client.stream(system, messages):
                if event["type"] == "delta":
                    streamed_ok = True
                    parts.append(event["text"])
                    yield {"type": "delta", "text": event["text"]}
                elif event["type"] == "usage":
                    input_tokens = event.get("input_tokens", 0)
                    output_tokens = event.get("output_tokens", 0)
                    model = event.get("model")
                elif event["type"] == "error":
                    error = event.get("error")
            if not streamed_ok:  # échec streaming → repli déterministe
                fallback = self._deterministic_answer(prep)
                parts = [fallback]
                yield {"type": "delta", "text": fallback}
        else:
            answer = (
                self._deterministic_answer(prep)
                if prep.mode == "generate"
                else (prep.answer or NO_RESULT_MESSAGE)
            )
            parts = [answer]
            yield {"type": "delta", "text": answer}

        answer = "".join(parts)
        execution_ms = int((time.perf_counter() - start) * 1000)

        memory.save_turn(
            db, prep.conversation, question=question, answer=answer,
            sources=prep.context.sources, focus=prep.result.focus,
        )
        self._log(
            db, prep, question, answer, prompt=prompt_text,
            execution_ms=execution_ms, input_tokens=input_tokens,
            output_tokens=output_tokens, model=model, error=error,
        )
        yield {"type": "done", "conversation_id": str(prep.conversation.id)}


ai_pipeline = AiPipeline()
