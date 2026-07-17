"""Client Claude (Anthropic) : génération, streaming, retry, quotas de jetons.

L'import du SDK est paresseux : l'application démarre même sans la librairie
ou sans clé API (le pipeline bascule alors sur une réponse déterministe).
"""
from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger("ai.claude")


@dataclass
class GenerationResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text)


class ClaudeClient:
    def __init__(self) -> None:
        self._client = None
        self._checked = False

    def _get_client(self):
        if self._checked:
            return self._client
        self._checked = True
        if not settings.ANTHROPIC_API_KEY:
            logger.info("ANTHROPIC_API_KEY absente : mode déterministe.")
            return None
        try:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except ImportError:
            logger.warning("SDK anthropic non installé : mode déterministe.")
            self._client = None
        return self._client

    @property
    def available(self) -> bool:
        return self._get_client() is not None

    def generate(self, system: str, messages: list[dict]) -> GenerationResult:
        client = self._get_client()
        if client is None:
            return GenerationResult(text="", error="Client IA indisponible.")

        last_error: str | None = None
        for attempt in range(1, settings.AI_MAX_RETRIES + 2):
            try:
                response = client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=settings.AI_MAX_TOKENS,
                    temperature=settings.AI_TEMPERATURE,
                    system=system,
                    messages=messages,
                )
                text = "".join(
                    block.text for block in response.content
                    if getattr(block, "type", None) == "text"
                )
                return GenerationResult(
                    text=text.strip(),
                    input_tokens=getattr(response.usage, "input_tokens", 0),
                    output_tokens=getattr(response.usage, "output_tokens", 0),
                    model=settings.ANTHROPIC_MODEL,
                )
            except Exception as exc:  # transitoire ou définitif
                last_error = str(exc)
                logger.warning("Échec Claude (tentative %s) : %s", attempt, exc)
                if attempt <= settings.AI_MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 8))
        return GenerationResult(text="", error=last_error or "Erreur inconnue.")

    def stream(self, system: str, messages: list[dict]) -> Iterator[dict]:
        """Diffuse des événements : {type: delta|usage|error, ...}."""
        client = self._get_client()
        if client is None:
            yield {"type": "error", "error": "Client IA indisponible."}
            return
        try:
            with client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                system=system,
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    yield {"type": "delta", "text": chunk}
                final = stream.get_final_message()
                yield {
                    "type": "usage",
                    "input_tokens": getattr(final.usage, "input_tokens", 0),
                    "output_tokens": getattr(final.usage, "output_tokens", 0),
                    "model": settings.ANTHROPIC_MODEL,
                }
        except Exception as exc:
            logger.warning("Échec streaming Claude : %s", exc)
            yield {"type": "error", "error": str(exc)}


claude_client = ClaudeClient()
