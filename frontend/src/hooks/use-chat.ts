"use client";

import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";

export interface AskPayload {
  question: string;
  conversationId?: string;
  attachmentIds?: string[];
}

export interface AskResponse {
  answer: string;
  conversationId: string;
  /** Références de la base ayant servi à construire la réponse. */
  sources: Array<{ type: string; id: string; label: string }>;
}

/**
 * Mutation d'envoi d'une question à l'assistant.
 * NOTE : la logique IA n'est pas encore implémentée côté backend ;
 * ce hook prépare uniquement le contrat d'API.
 */
export function useAskAssistant() {
  return useMutation({
    mutationFn: (payload: AskPayload) =>
      apiClient.post<AskResponse>(API_ENDPOINTS.chat.ask, payload),
  });
}
