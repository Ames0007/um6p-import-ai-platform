"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { LookupResponse } from "@/types/knowledge";

/**
 * Recherche instantanée par CONCEPT dans l'Index de connaissance (sans IA).
 * Renvoie des cartes structurées + éventuel aperçu chapitre.
 */
export function useKnowledgeLookup(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: ["knowledge-lookup", q],
    queryFn: () =>
      apiClient.get<LookupResponse>(
        `${API_ENDPOINTS.knowledge.lookup}?q=${encodeURIComponent(q)}&limit=12`
      ),
    enabled: q.length >= 1,
    staleTime: 60_000,
  });
}
