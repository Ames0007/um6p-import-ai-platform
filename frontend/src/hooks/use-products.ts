"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { Product } from "@/types/product";

/** Recherche dans le référentiel produits interne (PostgreSQL). */
export function useProductsSearch(query: string, enabled: boolean) {
  const q = query.trim();
  return useQuery({
    queryKey: ["products-search", q],
    queryFn: () =>
      apiClient.get<Product[]>(
        `${API_ENDPOINTS.products.search}?q=${encodeURIComponent(q)}`
      ),
    enabled: enabled && q.length >= 1,
    staleTime: 30_000,
  });
}
