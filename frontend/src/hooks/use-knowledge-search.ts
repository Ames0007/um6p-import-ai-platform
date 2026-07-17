"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { SearchResponse } from "@/types/knowledge";

/** Recherche dans la base de connaissances (activée quand `query` est non vide). */
export function useKnowledgeSearch(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: ["knowledge-search", q],
    queryFn: () =>
      apiClient.get<SearchResponse>(
        `${API_ENDPOINTS.knowledge.search}?q=${encodeURIComponent(q)}`
      ),
    enabled: q.length >= 2,
    staleTime: 30_000,
  });
}
