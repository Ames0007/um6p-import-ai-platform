"use client";

import * as React from "react";
import type {
  AssistantMeta,
  CopilotMessage,
  StreamEvent,
} from "@/types/chat";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

let counter = 0;
const nextId = () => `m${++counter}`;

/**
 * Gère une conversation avec le copilote : mémoire (conversation_id),
 * streaming SSE, et mise à jour incrémentale du dernier message assistant.
 */
export function useCopilot() {
  const [messages, setMessages] = React.useState<CopilotMessage[]>([]);
  const [isStreaming, setIsStreaming] = React.useState(false);
  const conversationId = React.useRef<string | null>(null);

  const patchAssistant = React.useCallback(
    (id: string, patch: Partial<CopilotMessage>) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
      );
    },
    []
  );

  const appendDelta = React.useCallback((id: string, text: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, content: m.content + text } : m
      )
    );
  }, []);

  const send = React.useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || isStreaming) return;

      const assistantId = nextId();
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", content: q },
        { id: assistantId, role: "assistant", content: "", streaming: true },
      ]);
      setIsStreaming(true);

      try {
        const res = await fetch(`${API_BASE}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: q,
            conversation_id: conversationId.current,
          }),
        });
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) >= 0) {
            const raw = buffer.slice(0, idx).trim();
            buffer = buffer.slice(idx + 2);
            if (!raw.startsWith("data:")) continue;
            const evt = JSON.parse(raw.slice(5).trim()) as StreamEvent;

            if (evt.type === "meta") {
              conversationId.current = evt.conversation_id;
              const meta: AssistantMeta = {
                intent: evt.intent,
                confidence: evt.confidence,
                sources: evt.sources,
                citations: evt.citations,
                candidates: evt.candidates,
                needs_clarification: evt.needs_clarification,
              };
              patchAssistant(assistantId, { meta });
            } else if (evt.type === "delta") {
              appendDelta(assistantId, evt.text);
            } else if (evt.type === "done") {
              conversationId.current = evt.conversation_id;
            } else if (evt.type === "error") {
              appendDelta(assistantId, `\n\n_Erreur : ${evt.error}_`);
            }
          }
        }
      } catch {
        patchAssistant(assistantId, {
          content:
            "Une erreur est survenue lors de la communication avec l'assistant. " +
            "Vérifiez que l'API est démarrée.",
        });
      } finally {
        patchAssistant(assistantId, { streaming: false });
        setIsStreaming(false);
      }
    },
    [isStreaming, appendDelta, patchAssistant]
  );

  return { messages, isStreaming, send };
}
