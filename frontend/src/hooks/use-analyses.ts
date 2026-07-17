"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type {
  AnalysisDetail,
  AnalysisDispatchResult,
  AnalysisListItem,
} from "@/types/compliance";

const KEY = ["analyses"] as const;
const ACTIVE = new Set(["en_attente", "en_cours"]);

export function useAnalyses() {
  return useQuery({
    queryKey: KEY,
    queryFn: () =>
      apiClient.get<AnalysisListItem[]>(API_ENDPOINTS.analysis.list),
    refetchInterval: (query) => {
      const data = query.state.data as AnalysisListItem[] | undefined;
      return data?.some((a) => ACTIVE.has(a.status)) ? 2000 : false;
    },
  });
}

export function useUploadInvoices() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return apiClient.post<AnalysisDispatchResult>(
        API_ENDPOINTS.analysis.upload,
        form
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useAnalysisDetail(id: string) {
  return useQuery({
    queryKey: ["analysis", id],
    queryFn: () =>
      apiClient.get<AnalysisDetail>(API_ENDPOINTS.analysis.byId(id)),
    refetchInterval: (query) => {
      const data = query.state.data as AnalysisDetail | undefined;
      return data && ACTIVE.has(data.status) ? 2000 : false;
    },
  });
}
