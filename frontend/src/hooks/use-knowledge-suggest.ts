"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { SuggestResponse } from "@/types/knowledge";

/** Débounce simple d'une valeur (autocomplétion). */
function useDebounced<T>(value: T, delay = 150): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

/** Suggestions d'autocomplétion (sans IA) depuis l'Index de connaissance. */
export function useKnowledgeSuggest(query: string, enabled = true) {
  const q = useDebounced(query.trim(), 150);
  return useQuery({
    queryKey: ["knowledge-suggest", q],
    queryFn: () =>
      apiClient.get<SuggestResponse>(
        `${API_ENDPOINTS.knowledge.suggest}?q=${encodeURIComponent(q)}&limit=8`
      ),
    enabled: enabled && q.length >= 2,
    staleTime: 30_000,
  });
}
